use std::env;
use std::ffi::OsStr;
use std::fs;
use std::path::{Component, Path, PathBuf};
use std::process::{Command, ExitCode};

use syn::spanned::Spanned;
use syn::visit::{self, Visit};
use syn::{Block, Expr, ImplItemFn, ItemFn, ReturnType, Signature, Stmt, TraitItemFn, Type};

const MAX_EXAMPLES: usize = 5;
const MAX_SOURCE_BYTES: u64 = 1_000_000;
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

fn lint_source(path: &str, source: &str) -> Result<Vec<Finding>, syn::Error> {
    let syntax = syn::parse_file(source)?;
    let mut visitor = ExplicitReturnVisitor {
        path,
        findings: Vec::new(),
    };
    visitor.visit_file(&syntax);
    Ok(visitor.findings)
}

fn lint_repository(root: &Path) -> Result<Vec<Finding>, String> {
    let mut findings = Vec::new();
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
            Ok(mut file_findings) => findings.append(&mut file_findings),
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

    findings.sort_by(|left, right| {
        (&left.path, left.line, &left.function).cmp(&(&right.path, right.line, &right.function))
    });
    Ok(findings)
}

fn escape_workflow_message(message: &str) -> String {
    message
        .replace('%', "%25")
        .replace('\r', "%0D")
        .replace('\n', "%0A")
}

fn emit_single_warning(findings: &[Finding]) {
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
    emit_single_warning(&findings);
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

    fn findings(source: &str) -> Vec<Finding> {
        lint_source("src/lib.rs", source).expect("test source should parse")
    }

    #[test]
    fn reports_only_non_unit_implicit_returns() {
        let actual = findings(
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
        let actual = findings(
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
        let actual = findings(
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
        let actual = findings(
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
}
