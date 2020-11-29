# Testing Celery tasks

## Docs

[Celery Canvas](https://docs.celeryproject.org/en/stable/userguide/canvas.html) offers 
synchronization primitives like chain, group, chord

[Testing](https://docs.celeryproject.org/en/stable/userguide/testing.html) describes how to perform
Celery testing using Pytest fixtures, unfortunately it doesn't work as described :/


## Possible approaches to testing

#### Unit testing (no eager mode) 
- pretty easy - just call task synchronously like a normal function, e.g. `result tasks.simple_task(42)`
- works fine as long as the tasks you test don't call any subtasks

#### Using CELERY_ALWAYS_EAGER
- enabling this setting makes all tasks run synchronously
- works well for simple cases, might be unnecessary when testing business logic that calls task doing something heavy
- ignores retries and countdown (calling with delay) 
- behaves like DFS - meaning it executes task delayed before finishing current task which can result in 
unexpected behaviour

#### Integration testing using worker thread
- nice solution for complex workflows but harder to do properly
- makes more guarantees about task flows (chains, groups etc) and the task contracts
- official docs are little help here

## How to use this repo
There are two tests module: one for testing tasks created with shared_task and another one with project's Celery app.
Most of interesting details are included in docstring of these two modules.

Run both with
```bash
$ docker-compose run --rm app sh test.sh
```
or directly invoking pytest
```bash
$ docker-compose run --rm app pytest -k some_test_or_module
```

Unfortunately calling all tests with single pytest invocation doesn't work. 
It's probably because `celery_session_worker` is used everywhere and it's session scoped. 
