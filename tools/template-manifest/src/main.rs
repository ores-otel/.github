use serde_json::json;
use sha2::{Digest,Sha256};
use std::{collections::BTreeMap,env,fs,path::{Path,PathBuf},process};
const SKIP:[&str;9]=[".build",".dart_tool",".gradle",".pytest_cache","__pycache__","build","coverage","dist","node_modules"];
fn skipped(s:&str)->bool{SKIP.contains(&s)||s=="target"}
fn visit(base:&Path,dir:&Path,files:&mut BTreeMap<String,String>)->Result<(),String>{
    for entry in fs::read_dir(dir).map_err(|e|format!("{}: {e}",dir.display()))?{
        let entry=entry.map_err(|e|e.to_string())?;
        let name=entry.file_name();
        if skipped(&name.to_string_lossy()){continue}
        let path=entry.path();
        let kind=entry.file_type().map_err(|e|e.to_string())?;
        if kind.is_symlink(){return Err(format!("template symlink is forbidden: {}",path.display()))}
        if kind.is_dir(){visit(base,&path,files)?}
        if kind.is_file(){
            let relative=path.strip_prefix(base).map_err(|e|e.to_string())?;
            let name=relative.to_str().ok_or("non-UTF8 relative template filename")?.replace(std::path::MAIN_SEPARATOR,"/");
            let bytes=fs::read(&path).map_err(|e|format!("{}: {e}",path.display()))?;
            let digest=Sha256::digest(bytes);
            let sha=digest.iter().map(|v|format!("{v:02x}")).collect::<String>();
            files.insert(name,sha);
        }
    }
    Ok(())
}
fn render(root:&Path,source:&str,template:&str)->Result<Vec<u8>,String>{
    if !root.is_dir(){return Err(format!("template directory missing: {}",root.display()))}
    let mut files=BTreeMap::new();
    visit(root,root,&mut files)?;
    if files.is_empty(){return Err(format!("template contains no files: {}",root.display()))}
    let data=json!({"files":files,"schema":"ores.otel.repository-template/v1","source":source,"template":template});
    let mut out=serde_json::to_vec_pretty(&data).map_err(|e|e.to_string())?;
    out.push(b'\n');
    Ok(out)
}
fn run()->Result<(),String>{
    let mut root=None::<PathBuf>;let mut template=None::<String>;let mut output=None::<PathBuf>;
    let mut source="ores-otel/.github".to_owned();let mut check=false;
    let mut args=env::args().skip(1);
    while let Some(arg)=args.next(){
        match arg.as_str(){
            "--template-root"=>root=Some(PathBuf::from(args.next().ok_or("missing --template-root argument")?)),
            "--template-id"=>template=Some(args.next().ok_or("missing --template-id argument")?),
            "--source"=>source=args.next().ok_or("missing --source argument")?,
            "--output"=>output=Some(PathBuf::from(args.next().ok_or("missing --output argument")?)),
            "--check"=>check=true,
            _=>return Err(format!("unknown argument: {arg}"))
        }
    }
    let root=root.ok_or("missing --template-root")?;
    let template=template.ok_or("missing --template-id")?;
    let output=output.ok_or("missing --output")?;
    let content=render(&root,&source,&template)?;
    if check{
        if fs::read(&output).ok().as_deref()!=Some(content.as_slice()){
            return Err(format!("template provenance manifest is stale: {}",output.display()))
        }
        println!("template provenance manifest is current: {}",output.display());
    }else{
        if let Some(parent)=output.parent(){fs::create_dir_all(parent).map_err(|e|e.to_string())?}
        fs::write(&output,content).map_err(|e|e.to_string())?;
        println!("rendered template provenance manifest: {}",output.display());
    }
    Ok(())
}
fn main(){if let Err(e)=run(){eprintln!("ERROR: {e}");process::exit(1)}}
#[cfg(test)] mod tests{
    use super::*;
    #[test]fn rejects_missing_template(){assert!(render(Path::new("/missing/nontemplate"),"source","template").is_err());}
    #[test]fn serialized_contract_fields(){
        let value=json!({"files":{"a":"abcd"},"schema":"ores.otel.repository-template/v1","source":"repo","template":"id"});
        let rendered=serde_json::to_string_pretty(&value).unwrap();
        assert!(rendered.contains("\"files\""));assert!(rendered.contains("\"schema\""));
        assert!(rendered.find("\"files\"")<rendered.find("\"source\""));
    }
    #[test]fn avoids_build_outputs(){for s in ["node_modules","target",".build"]{assert!(skipped(s))}}
}
