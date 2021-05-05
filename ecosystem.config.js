module.exports = {
  'apps': [
    {
      'name': 'sandpiper',
      'interpreter': 'pipenv',
      'interpreter_args': ['run', 'python', '-m'],
      'script': 'sandpiper',
      // script is a required field, so this is a hacky way to make it work

      'watch': false,

      'min_uptime': '5s',
      'max_restarts': 1,
      'restart_delay': 0,
      'autorestart': true
    }
  ]
};
