const child_process = require('child_process');
//const oled = child_process.fork(__dirname + '/oled_display.py',[],{execPath:'/usr/bin/python3',stdio:'ipc'});
const oled = child_process.spawn('/usr/bin/python3',[__dirname + '/oled_display.py'],{stdio:['ipc']});

oled.stdout.on('data', (data) => {
  console.log(`stdout: ${data}`);
});

oled.stderr.on('data', (data) => {
  console.log(`stderr: ${data}`);
});

oled.on('close', (code) => {
  console.log(`子进程退出码：${code}`);
});


setTimeout(function(){
   oled.send( 'world' )
},1000);

process.on('uncaughtException', function (err) { console.log('Caught exception: ' + err); }); 
