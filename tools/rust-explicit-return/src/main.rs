use std::collections::BTreeSet;
use std::env;
use std::ffi::OsStr;
use std::fs;
use std::path::{Component, Path, PathBuf};
use std::process::{Command, ExitCode};

use syn::spanned::Spanned;
use syn::visit::{self, Visit};
use syn::{
    Block, Expr, ImplItemFn, ItemFn, Local, Member, Pat, ReturnType, Signature, Stmt, TraitItemFn,
    Type,
};

const MAX_EXAMPLES: usize = 5;
const MAX_SOURCE_BYTES: u64 = 5_000_000;
const TELEMETRY_LEVEL_METHODS: &[&str] =
    &["trace", "debug", "info", "log", "warn", "error", "fatal"];
const TELEMETRY_TERMINAL_METHODS: &[&str] = &["send", "send_with_store"];
const TELEMETRY_SUPPRESSION: &str = "ores-source-policy: allow-missing-send";
const SKIPPED_COMPONENTS: &[&str] = &[
    ".cache",
    ".git",
    "build",
    "coverage",
    "dist",
    "fixtures",
    "generated",
    "node_modules",
    "target",
    "third_party",
    "vendor",
];

#[derive(Debug, Eq, PartialEq)]
struct Finding {
    path: String,
    line: usize,
    function: String,
}

#[derive(Debug, Eq, PartialEq)]
struct TelemetryFinding {
    path: String,
    line: usize,
}

#[derive(Debug, Default, Eq, PartialEq)]
struct SourceFindings {
    explicit_returns: Vec<Finding>,
    telemetry_missing_sends: Vec<TelemetryFinding>,
}

struct ExplicitReturnVisitor<'a> {
    path: &'a str,
    findings: Vec<Finding>,
}

impl ExplicitReturnVisitor<'_> {
    fn inspect(&mut self, signature: &Signature, block: &Block) {
        if !has_non_unit_return_type(signature) {
            return;
        }

        let Some(expression) = implicit_tail_expression(block) else {
            return;
        };

        self.findings.push(Finding {
            path: self.path.to_owned(),
            line: expression.span().start().line,
            function: signature.ident.to_string(),
        });
    }
}

impl<'ast> Visit<'ast> for ExplicitReturnVisitor<'_> {
    fn visit_item_fn(&mut self, function: &'ast ItemFn) {
        self.inspect(&function.sig, &function.block);
        visit::visit_item_fn(self, function);
    }

    fn visit_impl_item_fn(&mut self, function: &'ast ImplItemFn) {
        self.inspect(&function.sig, &function.block);
        visit::visit_impl_item_fn(self, function);
    }

    fn visit_trait_item_fn(&mut self, function: &'ast TraitItemFn) {
        if let Some(block) = &function.default {
            self.inspect(&function.sig, block);
        }
        visit::visit_trait_item_fn(self, function);
    }
}

struct TelemetryVisitor<'a> {
    path: &'a str,
    known_loggers: BTreeSet<String>,
    findings: Vec<TelemetryFinding>,
}

impl TelemetryVisitor<'_> {
    fn inspect_statement(&mut self, statement: &Stmt) {
        let Stmt::Expr(expression, Some(_)) = statement else {
            return;
        };

        let mut methods = Vec::new();
        let root = collect_method_chain(expression, &mut methods);
        let Some(level_index) = methods
            .iter()
            .position(|method| TELEMETRY_LEVEL_METHODS.contains(&method.as_str()))
        else {
            return;
        };
        if methods[level_index + 1..]
            .iter()
            .any(|method| TELEMETRY_TERMINAL_METHODS.contains(&method.as_str()))
        {
            return;
        }
        if !is_logger_producer(root, &self.known_loggers) {
            return;
        }

        self.findings.push(TelemetryFinding {
            path: self.path.to_owned(),
            line: expression.span().start().line,
        });
    }

    fn learn_local_logger(&mut self, local: &Local) {
        let Some(init) = &local.init else {
            return;
        };
        if !is_logger_producer(&init.expr, &self.known_loggers) {
            return;
        }
        if let Some(identifier) = binding_identifier(&local.pat) {
            self.known_loggers.insert(identifier);
        }
    }
}

impl<'ast> Visit<'ast> for TelemetryVisitor<'_> {
    fn visit_local(&mut self, local: &'ast Local) {
        self.learn_local_logger(local);
        visit::visit_local(self, local);
    }

    fn visit_stmt(&mut self, statement: &'ast Stmt) {
        self.inspect_statement(statement);
        visit::visit_stmt(self, statement);
    }
}

fn unwrap_expression(expression: &Expr) -> &Expr {
    match expression {
        Expr::Await(await_expression) => unwrap_expression(&await_expression.base),
        Expr::Group(group) => unwrap_expression(&group.expr),
        Expr::Paren(paren) => unwrap_expression(&paren.expr),
        Expr::Try(try_expression) => unwrap_expression(&try_expression.expr),
        _ => expression,
    }
}

fn collect_method_chain<'a>(expression: &'a Expr, methods: &mut Vec<String>) -> &'a Expr {
    let current = unwrap_expression(expression);
    if let Expr::MethodCall(method_call) = current {
        let root = collect_method_chain(&method_call.receiver, methods);
        methods.push(method_call.method.to_string());
        return root;
    }
    current
}

fn binding_identifier(pattern: &Pat) -> Option<String> {
    match pattern {
        Pat::Ident(identifier) => Some(identifier.ident.to_string()),
        Pat::Type(typed) => binding_identifier(&typed.pat),
        _ => None,
    }
}

fn path_last_identifier(expression: &Expr) -> Option<String> {
    match unwrap_expression(expression) {
        Expr::Path(path) => path
            .path
            .segments
            .last()
            .map(|segment| segment.ident.to_string()),
        Expr::Field(field) => match &field.member {
            Member::Named(identifier) => Some(identifier.to_string()),
            Member::Unnamed(_) => None,
        },
        _ => None,
    }
}

fn is_logger_constructor(function: &Expr) -> bool {
    let Expr::Path(path) = unwrap_expression(function) else {
        return false;
    };
    let segments = path.path.segments.iter().collect::<Vec<_>>();
    let Some(method) = segments.last() else {
        return false;
    };
    if !matches!(method.ident.to_string().as_str(), "new" | "default") {
        return false;
    }
    segments
        .iter()
        .rev()
        .nth(1)
        .is_some_and(|owner| owner.ident == "Logger")
}

fn is_logger_factory(function: &Expr) -> bool {
    path_last_identifier(function).is_some_and(|identifier| {
        matches!(
            identifier.as_str(),
            "create_logger"
                | "create_browser_logger"
                | "create_edge_logger"
                | "create_node_logger"
                | "create_bun_logger"
                | "create_deno_logger"
        )
    })
}

fn is_logger_producer(expression: &Expr, known_loggers: &BTreeSet<String>) -> bool {
    let current = unwrap_expression(expression);
    if path_last_identifier(current).is_some_and(|identifier| {
        known_loggers.contains(&identifier)
            || matches!(identifier.as_str(), "log" | "logger" | "ddlog")
    }) {
        return true;
    }

    match current {
        Expr::Call(call) => is_logger_constructor(&call.func) || is_logger_factory(&call.func),
        Expr::MethodCall(method_call) if method_call.method == "anew" => {
            is_logger_producer(&method_call.receiver, known_loggers)
        }
        _ => false,
    }
}

fn has_telemetry_suppression(source: &str, line: usize) -> bool {
    let lines = source.lines().collect::<Vec<_>>();
    let current = line.checked_sub(1).and_then(|index| lines.get(index));
    let previous = line.checked_sub(2).and_then(|index| lines.get(index));
    current
        .into_iter()
        .chain(previous)
        .any(|candidate| candidate.contains(TELEMETRY_SUPPRESSION))
}

fn has_non_unit_return_type(signature: &Signature) -> bool {
    match &signature.output {
        ReturnType::Default => false,
        ReturnType::Type(_, return_type) => {
            !matches!(
                return_type.as_ref(),
                Type::Tuple(tuple) if tuple.elems.is_empty()
            ) && !matches!(return_type.as_ref(), Type::Never(_))
        }
    }
}

fn implicit_tail_expression(block: &Block) -> Option<&Expr> {
    match block.stmts.last() {
        Some(Stmt::Expr(expression, None)) if !returns_explicitly(expression) => Some(expression),
        _ => None,
    }
}

fn returns_explicitly(expression: &Expr) -> bool {
    match expression {
        // A macro can expand to `return`, so treating it as an implicit return would create
        // an unresolvable false positive without compiler expansion information.
        Expr::Return(_) | Expr::Macro(_) => true,
        Expr::Block(block) => block
            .block
            .stmts
            .last()
            .is_some_and(statement_returns_explicitly),
        Expr::Group(group) => returns_explicitly(&group.expr),
        Expr::Paren(paren) => returns_explicitly(&paren.expr),
        Expr::Unsafe(unsafe_expression) => unsafe_expression
            .block
            .stmts
            .last()
            .is_some_and(statement_returns_explicitly),
        Expr::If(if_expression) => {
            if_expression
                .then_branch
                .stmts
                .last()
                .is_some_and(statement_returns_explicitly)
                && if_expression
                    .else_branch
                    .as_ref()
                    .is_some_and(|(_, else_expression)| returns_explicitly(else_expression))
        }
        Expr::Match(match_expression) => {
            !match_expression.arms.is_empty()
                && match_expression
                    .arms
                    .iter()
                    .all(|arm| returns_explicitly(&arm.body))
        }
        _ => false,
    }
}

fn statement_returns_explicitly(statement: &Stmt) -> bool {
    matches!(statement, Stmt::Expr(expression, _) if returns_explicitly(expression))
}

fn is_skipped(path: &Path) -> bool {
    path.components().any(|component| {
        let Component::Normal(value) = component else {
            return false;
        };
        SKIPPED_COMPONENTS
            .iter()
            .any(|skipped| value == OsStr::new(skipped))
    })
}

fn tracked_rust_files(root: &Path) -> Result<Vec<PathBuf>, String> {
    let output = Command::new("git")
        .arg("-C")
        .arg(root)
        .args(["ls-files", "-z", "--", "*.rs"])
        .output()
        .map_err(|error| format!("could not start git: {error}"))?;

    if !output.status.success() {
        return Err(format!(
            "git ls-files failed: {}",
            String::from_utf8_lossy(&output.stderr).trim()
        ));
    }

    let mut paths = output
        .stdout
        .split(|byte| *byte == 0)
        .filter(|bytes| !bytes.is_empty())
        .map(|bytes| PathBuf::from(String::from_utf8_lossy(bytes).into_owned()))
        .filter(|path| !is_skipped(path))
        .collect::<Vec<_>>();
    paths.sort();
    Ok(paths)
}

fn lint_source(path: &str, source: &str) -> Result<SourceFindings, syn::Error> {
    let syntax = syn::parse_file(source)?;
    let mut explicit_return_visitor = ExplicitReturnVisitor {
        path,
        findings: Vec::new(),
    };
    explicit_return_visitor.visit_file(&syntax);

    let mut telemetry_visitor = TelemetryVisitor {
        path,
        known_loggers: ["log", "logger", "ddlog"]
            .into_iter()
            .map(str::to_owned)
            .collect(),
        findings: Vec::new(),
    };
    telemetry_visitor.visit_file(&syntax);
    telemetry_visitor
        .findings
        .retain(|finding| !has_telemetry_suppression(source, finding.line));

    Ok(SourceFindings {
        explicit_returns: explicit_return_visitor.findings,
        telemetry_missing_sends: telemetry_visitor.findings,
    })
}

fn lint_repository(root: &Path) -> Result<SourceFindings, String> {
    let mut findings = SourceFindings::default();
    let mut parse_errors = Vec::new();

    for relative_path in tracked_rust_files(root)? {
        let display_path = relative_path.to_string_lossy().into_owned();
        let absolute_path = root.join(&relative_path);
        let metadata = match fs::symlink_metadata(&absolute_path) {
            Ok(metadata) => metadata,
            Err(error) => {
                parse_errors.push(format!("{display_path}: {error}"));
                continue;
            }
        };
        if !metadata.is_file() {
            continue;
        }
        if metadata.len() > MAX_SOURCE_BYTES {
            parse_errors.push(format!(
                "{display_path}: tracked Rust source exceeds {MAX_SOURCE_BYTES} bytes"
            ));
            continue;
        }
        let source = match fs::read_to_string(&absolute_path) {
            Ok(source) => source,
            Err(error) => {
                parse_errors.push(format!("{display_path}: {error}"));
                continue;
            }
        };

        match lint_source(&display_path, &source) {
            Ok(mut file_findings) => {
                findings
                    .explicit_returns
                    .append(&mut file_findings.explicit_returns);
                findings
                    .telemetry_missing_sends
                    .append(&mut file_findings.telemetry_missing_sends);
            }
            Err(error) => parse_errors.push(format!("{display_path}: {error}")),
        }
    }

    if !parse_errors.is_empty() {
        return Err(format!(
            "could not parse {} tracked Rust file(s): {}",
            parse_errors.len(),
            parse_errors
                .iter()
                .take(MAX_EXAMPLES)
                .cloned()
                .collect::<Vec<_>>()
                .join("; ")
        ));
    }

    findings.explicit_returns.sort_by(|left, right| {
        (&left.path, left.line, &left.function).cmp(&(&right.path, right.line, &right.function))
    });
    findings
        .telemetry_missing_sends
        .sort_by(|left, right| (&left.path, left.line).cmp(&(&right.path, right.line)));
    Ok(findings)
}

fn escape_workflow_message(message: &str) -> String {
    message
        .replace('%', "%25")
        .replace('\r', "%0D")
        .replace('\n', "%0A")
}

fn emit_explicit_return_warning(findings: &[Finding]) {
    if findings.is_empty() {
        println!("Rust explicit-return policy: no implicit function returns found.");
        return;
    }

    let examples = findings
        .iter()
        .take(MAX_EXAMPLES)
        .map(|finding| format!("{}:{} ({})", finding.path, finding.line, finding.function))
        .collect::<Vec<_>>()
        .join("; ");
    let message = format!(
        "Found {} function(s) with an implicit non-unit return. Prefer an explicit `return` statement. Showing at most {} example(s): {}",
        findings.len(),
        MAX_EXAMPLES,
        examples
    );

    if env::var_os("GITHUB_ACTIONS").is_some() {
        println!(
            "::warning title=Rust explicit-return policy::{}",
            escape_workflow_message(&message)
        );
    } else {
        println!("warning: {message}");
    }
}

fn emit_telemetry_warning(findings: &[TelemetryFinding]) {
    if findings.is_empty() {
        println!("Rust telemetry policy: no unfinished Ores logger chains found.");
        return;
    }

    let examples = findings
        .iter()
        .take(MAX_EXAMPLES)
        .map(|finding| format!("{}:{}", finding.path, finding.line))
        .collect::<Vec<_>>()
        .join("; ");
    let message = format!(
        "Found {} standalone Ores telemetry event(s) without a terminal `.send()` or `.send_with_store(...)`. Showing at most {} example(s): {}. Suppress an intentional auto-send on the same or preceding line with `// {}`.",
        findings.len(),
        MAX_EXAMPLES,
        examples,
        TELEMETRY_SUPPRESSION
    );

    if env::var_os("GITHUB_ACTIONS").is_some() {
        println!(
            "::warning title=Rust Ores telemetry policy::{}",
            escape_workflow_message(&message)
        );
    } else {
        println!("warning: {message}");
    }
}

fn run() -> Result<(), String> {
    let root = match env::args_os().nth(1) {
        Some(path) => PathBuf::from(path),
        None => env::current_dir().map_err(|error| format!("could not read cwd: {error}"))?,
    };

    if !root.is_dir() {
        return Err(format!(
            "repository root does not exist: {}",
            root.display()
        ));
    }

    let findings = lint_repository(&root)?;
    emit_explicit_return_warning(&findings.explicit_returns);
    emit_telemetry_warning(&findings.telemetry_missing_sends);
    Ok(())
}

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("Rust explicit-return policy failed: {error}");
            ExitCode::FAILURE
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn explicit_return_findings(source: &str) -> Vec<Finding> {
        lint_source("src/lib.rs", source)
            .expect("test source should parse")
            .explicit_returns
    }

    fn telemetry_findings(source: &str) -> Vec<TelemetryFinding> {
        lint_source("src/lib.rs", source)
            .expect("test source should parse")
            .telemetry_missing_sends
    }

    #[test]
    fn reports_only_non_unit_implicit_returns() {
        let actual = explicit_return_findings(
            r#"
            fn implicit() -> usize { 42 }
            fn explicit() -> usize { return 42; }
            fn unit_default() { println!("ok"); }
            fn unit_named() -> () { println!("ok"); }
            fn never() -> ! { panic!("done") }
            "#,
        );

        assert_eq!(actual.len(), 1);
        assert_eq!(actual[0].function, "implicit");
    }

    #[test]
    fn reports_methods_and_trait_defaults() {
        let actual = explicit_return_findings(
            r"
            trait Value { fn value(&self) -> usize { 1 } }
            struct Number;
            impl Number { fn value(&self) -> usize { 2 } }
            ",
        );

        assert_eq!(actual.len(), 2);
        assert!(actual.iter().all(|finding| finding.function == "value"));
    }

    #[test]
    fn accepts_branches_that_all_return_explicitly() {
        let actual = explicit_return_findings(
            r"
            fn conditional(value: bool) -> usize {
                if value { return 1; } else { return 2; }
            }
            fn matched(value: bool) -> usize {
                match value { true => return 1, false => return 2 }
            }
            ",
        );

        assert!(actual.is_empty());
    }

    #[test]
    fn reports_value_producing_control_flow() {
        let actual = explicit_return_findings(
            r"
            fn conditional(value: bool) -> usize {
                if value { 1 } else { 2 }
            }
            fn matched(value: bool) -> usize {
                match value { true => 1, false => 2 }
            }
            ",
        );

        assert_eq!(actual.len(), 2);
    }

    #[test]
    fn workflow_messages_are_command_safe() {
        assert_eq!(escape_workflow_message("a%b\nc\r"), "a%25b%0Ac%0D");
    }

    #[test]
    fn reports_unfinished_ores_telemetry_chains() {
        let actual = telemetry_findings(
            r#"
            fn emit(options: Options) {
                let telemetry = Logger::new(options);
                telemetry.info(vec![json!("missing")]);
                telemetry.error(vec![json!("also missing")]).add_fields(fields);
            }
            "#,
        );

        assert_eq!(actual.len(), 2);
    }

    #[test]
    fn accepts_sent_deferred_returned_and_unrelated_builders() {
        let actual = telemetry_findings(
            r#"
            fn emit(logger: Logger, query: Query) -> Event {
                logger.info(vec![json!("sent")]).send();
                logger.warn(vec![json!("stored")]).send_with_store(true);
                let deferred = logger.error(vec![json!("sent later")]);
                consume(deferred);
                query.info("ordinary builder").where_clause("active");
                return logger.debug(vec![json!("returned")]);
            }
            "#,
        );

        assert!(actual.is_empty());
    }

    #[test]
    fn recognizes_inline_constructors_child_loggers_and_wrappers() {
        let actual = telemetry_findings(
            r"
            fn emit(options: Options) -> Result<(), Error> {
                next_loggers::Logger::new(options).info(vec![]);
                let logger = create_logger();
                let child = logger.anew(Default::default());
                child.warn(vec![]);
                (logger.error(vec![]).send())?;
                return Ok(());
            }
            ",
        );

        assert_eq!(actual.len(), 2);
    }

    #[test]
    fn ignores_macros_and_honors_targeted_suppression() {
        let actual = telemetry_findings(
            r#"
            fn emit(logger: Logger) {
                emit!(logger.info(vec![]));
                // ores-source-policy: allow-missing-send
                logger.warn(vec![json!("auto-sent")]);
            }
            "#,
        );

        assert!(actual.is_empty());
    }
}
