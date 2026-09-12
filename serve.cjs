const http=require('node:http'),fs=require('node:fs'),path=require('node:path');
const {spawnSync}=require('node:child_process');
const root=__dirname,output=path.join(root,'_site'),port=Number(process.env.PORT||8764);
function build(){return spawnSync(process.execPath,[path.join(root,'build.cjs')],{cwd:root,stdio:'inherit'}).status===0;}
if(!build())process.exit(1);
const mime={'.html':'text/html; charset=utf-8','.css':'text/css','.js':'text/javascript','.svg':'image/svg+xml','.woff2':'font/woff2','.woff':'font/woff','.png':'image/png','.json':'application/json'};
const server=http.createServer((req,res)=>{let url;try{url=decodeURIComponent(new URL(req.url,'http://localhost').pathname);}catch{res.writeHead(400);return res.end();}const file=path.resolve(output,'.'+(url==='/'?'/index.html':url)),relative=path.relative(output,file);if(relative.startsWith('..')||relative.split(path.sep).some(p=>p.startsWith('.'))){res.writeHead(403);return res.end();}fs.stat(file,(err,st)=>{if(err||!st.isFile()){res.writeHead(404);return res.end('Not found');}res.writeHead(200,{'Content-Type':mime[path.extname(file)]||'application/octet-stream','Cache-Control':'no-cache'});fs.createReadStream(file).pipe(res);});});
server.on('error',e=>{console.error(e.message);process.exit(1);});
server.listen(port,'127.0.0.1',()=>console.log(`Preview: http://127.0.0.1:${port}`));
let timer;const watcher=fs.watch(root,{recursive:true},(_,name)=>{if(!name||!(/^(src|content|assets)\//.test(name)||/^(style.css|site.config.json)$/.test(name)))return;clearTimeout(timer);timer=setTimeout(build,350);});
process.on('SIGINT',()=>{watcher.close();server.close(()=>process.exit());});
