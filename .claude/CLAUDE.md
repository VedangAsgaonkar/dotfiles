# Compute resources

Run lightweight commands directly.
For anything else, submit a slurm job using the `roach` skill.


# Files and dependencies

Use pixi environments for dependencies.

Use `~/scratch/<git_repo_name>/<expt_name>`
for experiment data and outputs.
Do NOT create any files or directories in `~/scratch`
or `~/` unless explicitly asked,
including as output files for your scripts.
Use `/tmp` for anything that need not be pushed to github.


# User input

If blocked on user input, send a push notification.


# Coding style

No comments. No docstrings. Code says what it does; git says what changed.

# Experimentation style
Here are some tips on how to experiment quickly:
- Caching: If some intermediate state is expected to be re-used, cache it. Be aware of how much disk that takes up
- Pipelining: If there are many similar processes, and each can be broken into subtasks, we can pipeline the subtasks
- Concurrency: When waiting for something to finish, put it in the background, put a watcher on it to interrupt you when it is done, and continue working on something else
- Parallelism: When you have multiple subagents / processes / CPUs / GPUs available, parallelize independent things as far as possible. Make sure they are truly independent, beware of contentions
- Out of order processing: If there is some task running, the future tasks that do not depend on it need not wait on it. If there is no dependency, we can execute out of order
- Speculative execution: If something is expected to succeed (some check / experiment etc.), continue working as if it has succeeded. Make sure you are aware of the cost of having to cancel / undo stuff because of a failed prediction.
- Prefetching: If you expect some artefact / object to be useful in the future, and it will take time to generate / download / fetch, you can prefetch it in the background.
