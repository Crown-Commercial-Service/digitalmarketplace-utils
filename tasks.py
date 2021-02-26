from invoke import task

from dmdevtools.invoke_tasks import library_tasks as ns


@task(ns["virtualenv"], ns["requirements_dev"])
def test_mypy(c):
    c.run("mypy dmutils/")


ns.add_task(test_mypy)
ns["test"].pre.insert(-1, test_mypy)
