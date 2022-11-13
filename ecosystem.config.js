// Hey. So I spent a while trying to get this to work on Windows.
// After migrating to pipenv, it's kept spawning an extra python
// console window. It was kind of a waste of time because I'm going
// to be running sandpiper on linux.
// 
// However, I found that the console window could be closed
// while leaving sandpiper running by killing the "conhost" child
// process of pipenv. So, whoever you are reading this, if you
// need to run sandpiper on windows without an extra window....
// just kill conhost. and I'm sorry for any pain this caused. :(
// I'm not spending any more time on this

let shell;
let args;
const command = 'poetry run python -m sandpiper';

switch (process.platform) {
    case 'win32':
        shell = 'cmd';
        args = ['/C', command];
        break
    case 'linux':
    case 'darwin':
        shell = '/bin/bash';
        args = ['-c', command];
        break;
    default:
        console.warn(
            `WARNING: Unexpected platform ${process.platform}, assuming a `
            + `Unix-like system.`
        );
        shell = '/bin/bash';
        args = ['-c', command];
}

module.exports = {
    apps: [
        {
            name: 'sandpiper',
            script: shell,
            args: args,

            watch: false,

            min_uptime: '5s',
            max_restarts: 3,
            restart_delay: 0,
            autorestart: true
        }
    ]
};
