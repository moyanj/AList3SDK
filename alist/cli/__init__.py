import asyncclick as click

from . import auth


@click.group()
async def cli():
    """
    Alist CLI
    """
    pass


@cli.group(name="auth", help="Authentication commands")
async def cli_auth():
    pass


@cli_auth.command(help="Add a new user", name="add")
@click.argument("uri")
@click.option("--default", "-d", is_flag=True, help="Set as default user")
@click.option("--tag", "-t", help="User Tag", default=None, required=False)
@click.option("--cover", "-c", is_flag=True, help="Cover existing user")
async def auth_add(**kwargs):
    await auth.add_user(**kwargs)


@cli_auth.command(help="Remove a user", name="rm")
@click.argument("un")
def auth_rm(un):
    auth.remove_user(un)


@cli_auth.command(help="List all users", name="ls")
async def auth_ls():
    auth.list_users()


if __name__ == "__main__":
    cli()
