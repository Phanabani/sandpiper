let interpreter;

switch (process.platform) {
  case 'win32':
    interpreter = 'venv/Scripts/pythonw.exe';
    break
  case 'linux':
  case 'darwin':
    interpreter = 'venv/bin/python';
    break;
  default:
    console.warn(`WARNING: Unexpected platform ${process.platform}`);
    interpreter = 'venv/bin/python';
}

module.exports = {
  'apps': [
    {
      'name': 'sandpiper',
      'script': interpreter,
      'args': ['-m', 'sandpiper'],

      'watch': false,

      'min_uptime': '5s',
      'max_restarts': 3,
      'restart_delay': 0,
      'autorestart': true
    }
  ]
};
