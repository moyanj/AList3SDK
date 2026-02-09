import asyncclick as click

from . import auth, fs


@click.group()
async def cli():
    """
    Alist CLI
    """
    pass


@cli.command(help="List files")
@click.argument("path", default="/")
@click.option("--user", "-u", help="Username")
async def ls(path, user):
    await fs.ls(path, user)


@cli.command(help="Create directory")
@click.argument("path")
@click.option("--user", "-u", help="Username")
async def mkdir(path, user):
    await fs.mkdir(path, user)


@cli.command(help="Remove file or directory")
@click.argument("path")
@click.option("--dir", "-d", is_flag=True, help="Is a directory")
@click.option("--user", "-u", help="Username")
async def rm(path, dir, user):
    await fs.rm(path, dir, user)


@cli.command(help="Upload file")
@click.argument("local")
@click.argument("remote")
@click.option("--user", "-u", help="Username")
async def upload(local, remote, user):
    await fs.upload(local, remote, user)


@cli.command(help="Download file")
@click.argument("remote")
@click.argument("local")
@click.option("--user", "-u", help="Username")
async def download(remote, local, user):
    await fs.download(remote, local, user)


@cli.command(help="Copy file")
@click.argument("src")
@click.argument("dst")
@click.option("--user", "-u", help="Username")
async def cp(src, dst, user):
    await fs.cp(src, dst, user)


@cli.command(help="Move file")
@click.argument("src")
@click.argument("dst")
@click.option("--user", "-u", help="Username")
async def mv(src, dst, user):
    await fs.mv(src, dst, user)


@cli.command(help="Show current user info", name="me")
@click.option("--user", "-u", help="Username")
async def info_me(user):
    await fs.me(user)


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
