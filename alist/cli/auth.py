import os
import pickle

from rich import box
from rich.table import Table

from alist import AList, AListUser

from ._data import console, dirs


async def add_user(uri, default, tag, cover):
    """
    添加用户

    Args:
        uri (str): 用户 URI，格式为 username:password@endpoint。
        default (bool): 是否将用户标记为默认用户。
        tag (str): 用户标签。
        cover (bool): 是否覆盖已存在的用户。
    """
    try:
        user, endpoint = AListUser.from_uri(uri)

        if ".__default" in user.un:
            console.print(
                "[bold red]✗ 用户名非法:[/] 不能包含保留字符 [bold]'.__default'[/]，请修改后重试"
            )
            return

        auth_files = os.listdir(dirs.auths)
        user_exists = user.un in auth_files
        default_user_exists = f"{user.un}.__default" in auth_files

        if (user_exists or default_user_exists) and not cover:
            console.print(
                f"[yellow]⚠ 用户存在:[/] [bold]{user.un}[/] 已存在，使用 [cyan]--cover[/] 覆盖"
            )
            return

        al = AList(endpoint)
        if not await al.test():
            console.print(
                f"[bold red]⛔ 连接失败:[/] 无法访问 [underline]{endpoint}[/]"
            )
            return

        # 唯一默认用户机制
        if default:
            removed_defaults = []
            for filename in os.listdir(dirs.auths):
                if filename.endswith(".__default"):
                    old_user = filename[: -len(".__default")]
                    os.remove(os.path.join(dirs.auths, filename))
                    removed_defaults.append(old_user)

            if removed_defaults:
                console.print(
                    f"[yellow]⚠ 已清除旧默认用户:[/] {', '.join(removed_defaults)}"
                )

        user_data = {
            "tag": tag,
            "endpoint": endpoint,
            "user": user.dumps(),
        }

        user_path = os.path.join(dirs.auths, user.un)
        if default:
            user_path += ".__default"

        with open(user_path, "wb") as f:
            pickle.dump(user_data, f)

        success_msg = f"[bold green]✓ 成功添加 {'[magenta]默认[/] ' if default else ''}用户:[/] [bold]{user.un}[/]"
        if tag:
            success_msg += f" 标签: [cyan]{tag}[/]"
        console.print(success_msg)

    except ValueError as e:
        console.print(
            f"[bold red]✘ 格式错误:[/] {e}，正确格式应为 [italic]username:password@http://domain.com[/]"
        )
    except Exception as e:
        console.print(f"[bold red]‼ 未捕获异常:[/] {type(e).__name__} - {str(e)}")


def remove_user(username):
    exists = os.listdir(dirs.auths)
    default_file = f"{username}.__default"
    regular_file = username

    if default_file in exists:
        os.remove(os.path.join(dirs.auths, default_file))
        console.print(f"[bold green]✓ 已移除默认用户:[/] [magenta]{username}[/]")
    elif regular_file in exists:
        os.remove(os.path.join(dirs.auths, regular_file))
        console.print(f"[bold green]✓ 已移除普通用户:[/] [cyan]{username}[/]")
    else:
        console.print(f"[yellow]⚠ 用户不存在:[/] 未找到 [italic]{username}[/] 的账户")


def list_users():
    """
    列出所有已注册用户
    """
    try:
        auth_dir = dirs.auths

        # 检查用户目录是否存在
        if not os.path.isdir(auth_dir):
            console.print("[yellow]⚠ 用户目录未初始化[/]")
            return

        user_files = os.listdir(auth_dir)
        if not user_files:
            console.print("[dim]暂无注册用户[/]")
            return

        # 创建表格
        table = Table(
            show_header=True,
            header_style="bold cyan",
            box=box.ROUNDED,
        )
        table.add_column("用户名", style="bold", min_width=15)
        table.add_column("类型", justify="center", width=8)
        table.add_column("标签", style="green", min_width=10)
        table.add_column("服务地址", style="dim blue")

        # 解析用户文件
        for filename in sorted(
            user_files, key=lambda x: (not x.endswith(".__default"), x)
        ):
            is_default = filename.endswith(".__default")
            username = filename[: -len(".__default")] if is_default else filename

            try:
                with open(os.path.join(auth_dir, filename), "rb") as f:
                    data = pickle.load(f)
                    tag = data.get("tag", "[dim]无")
                    endpoint = data.get("endpoint", "[red]未知")

            except Exception as e:
                tag = "[red]数据损坏"
                endpoint = f"[red]{str(e)[:30]}"

            # 处理默认用户显示
            user_type = "[bold magenta]默认[/]" if is_default else "[cyan]普通"

            table.add_row(f"[bold]{username}[/]", user_type, tag, endpoint)

        console.print(table)

    except PermissionError:
        console.print("[red]⛔ 权限不足: 无法读取用户目录[/]")
    except Exception as e:
        console.print(f"[red]‼ 列表加载失败: {type(e).__name__} - {str(e)}[/]")
