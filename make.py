import sys
import os
import subprocess
import traceback
from pathlib import Path
import shutil
import argparse
import re

_dir = os.path.dirname(__file__)
_dir_dir = os.path.dirname(_dir)
sys.path.append(_dir_dir)
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'utils'))
__package__ = os.path.basename(_dir)
del _dir
del _dir_dir

from .src.utils.printx import *

# ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰

addon_name = 'wire_fix_ime'
addon_full_name = 'wire_ext_blender_fix_ime'

prj_dir = Path(__file__).parent

def make():
    def boo(v):
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return False if v.lower() in ['false', 'off'] else True
        return True

    parser_parent = argparse.ArgumentParser(add_help=False)

    parser = argparse.ArgumentParser(
        prog='make', description="生成工具")

    subparsers = parser.add_subparsers(help="", dest='verbo')

    subparser = subparsers.add_parser('build', help="生成",
        parents=[parser_parent])
    subparser.add_argument('-c', '--config', choices=['debug', 'release'], default='debug', required=False,
        help="配置")
    subparser.add_argument('--vsdev', type=str, required=True,
        help="VsDevCmd.bat 文件的路径（用于 build 命令），"
        "如：C:/Program Files (x86)/Microsoft Visual Studio/2022/BuildTools/Common7/Tools/VsDevCmd.bat")

    subparser = subparsers.add_parser('link', parents=[parser_parent],
        help="链接到 Blender 的 addons 目录")
    subparser.add_argument('-c', '--config', choices=['debug', 'release'], default='debug', required=False,
        help="配置")
    subparser.add_argument('--blender-addon-dir', type=str, required=True,
        help="Blender 插件目录")

    subparser = subparsers.add_parser('run', parents=[parser_parent],
        help="运行 Blender")
    subparser.add_argument('--blender-dir', type=str, required=True,
        help="Blender 目录")
    subparser.add_argument('--blender-user-dir', type=str, required=False, default=None,
        help="Blender 用户目录")
    subparser.add_argument('--use_wt', type=boo, required=False, default=False,
        help="使用 Windows Terminal")

    subparser = subparsers.add_parser('clean', parents=[parser_parent],
        help="清理")

    subparser = subparsers.add_parser('pack', parents=[parser_parent],
        help="打包")

    args, _ = parser.parse_known_args()

    try:

        if args.verbo == 'build':
            build(args)

        elif args.verbo == 'link':
            link(args)

        elif args.verbo == 'run':
            run(args)

        elif args.verbo == 'clean':
            clean(args)

        elif args.verbo == 'pack':
            pack(args)

        else:
            printx("请指定一个操作")
            printx("----------")
            parser.print_help()

        printx("\n执行结束")
        printx("----------")

    except:
        traceback.print_exc()

    pass

def build(args):

    path_vsdevcmd = Path(args.vsdev)

    if args.config == 'debug':
        int_dir = prj_dir.joinpath('xbuild', 'debug')
        out_dir = prj_dir.joinpath('xdebug')
    elif args.config == 'release':
        int_dir = prj_dir.joinpath('xbuild', 'release')
        out_dir = prj_dir.joinpath('xrelease')

    os.makedirs(int_dir, exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)

    if args.config == 'release':
        for _name in os.listdir(out_dir):
            _path = out_dir.joinpath(_name)
            if _path.is_file():
                os.remove(_path)
            else:
                shutil.rmtree(_path)

    # 生成 DLL

    if not path_vsdevcmd.exists():
        printx("找不到：%s" % path_vsdevcmd)
        printx("请使用 --vsdev 选项指定 VsDevCmd.bat 的路径")

    else:
        path_vsxproj = prj_dir.joinpath('src', 'native', 'main.vcxproj')
        path_src_dir = prj_dir.joinpath('src', 'native')
        path_int_dir = int_dir.joinpath('int')
        path_out_dir = int_dir.joinpath('out')

        need_to_rebuild = True
        if path_out_dir.exists():

            mtime_src = 0
            for _name in os.listdir(path_src_dir):
                if _name.endswith('.py'):
                    continue
                mtime_src = max(mtime_src, os.path.getmtime(path_src_dir.joinpath(_name)))

            mtime_out = 0
            for _name in os.listdir(path_out_dir):
                if _name.endswith('.py'):
                    continue
                mtime_out = max(mtime_out, os.path.getmtime(path_out_dir.joinpath(_name)))

            if mtime_out > mtime_src:
                need_to_rebuild = False

        if need_to_rebuild:

            props: list[str] = []
            props.append('Configuration={}'.format(args.config.capitalize()))
            props.append('Platform=x64')
            props.append('IntDir={}\\'.format(path_int_dir))  # 必须以斜杠结尾
            props.append('OutDir={}\\'.format(path_out_dir))

            cmd = [
                'chcp', '65001', '&&',
                'call', path_vsdevcmd, '&&',
                'msbuild.exe', path_vsxproj, '-property:' + ";".join(props)
            ]
            printx("生成命令: %s\n" % cmd)

            p = subprocess.Popen(cmd, shell=True)
            (output, err) = p.communicate()
            p_status = p.wait()

            printx("\n")

        else:
            printx("无需重新编译")
            printx("\n")

    # 复制文件

    files = [  # (src, dst)
        (['src', 'debug', '__init__.py'], ['debug', '__init__.py']),
        (['src', 'debug', 'mark.py'], ['debug', 'mark.py']),
        (['src', 'native', '__init__.py'], ['native', '__init__.py']),
        (['xbuild', args.config, 'out', f'{addon_name}.dll'], ['native', f'{addon_name}.dll']),
        (['src', 'utils', '__init__.py'], ['utils', '__init__.py']),
        (['src', 'utils', 'printx.py'], ['utils', 'printx.py']),
        (['src', '__init__.py'], ['__init__.py']),
        (['src', 'ime.py'], ['ime.py']),
        (['src', 'main.py'], ['main.py']),
        (['src', 'prefs.py'], ['prefs.py']),
        #
        (['LICENSE'], []),
        (['docs', 'README_package.md'], ['README.md']),
    ]

    if args.config == 'debug':
        files.append((['src', 'debug', 'mark_locale.py'], ['debug', 'mark_locale.py']))
        files.append((['src', 'dev', '__init__.py'], ['dev', '__init__.py']))
        files.append((['xbuild', args.config, 'out', f'{addon_name}.pdb'], ['native', f'{addon_name}.pdb']))
        
    for _src, _dst in files:
        if _src is None:
            continue

        if not _dst:
            _dst = _src

        _src_path = prj_dir.joinpath(*_src)
        _dst_path = out_dir.joinpath(*_dst)
        _src_exists = _src_path.exists()
        _dst_exists = _dst_path.exists()

        if _src_exists:
            if _src_path.is_file():
                if not _dst_exists or _dst_path.stat().st_mtime < _src_path.stat().st_mtime:
                    printx(CCFA, "复制文件：%s" % str(_src))

                    # Blender 3.0（Python 3.9）不支持该特性
                    if _src_path.name.endswith('.py'):
                        with open(_src_path, 'r', encoding='utf-8') as _file:
                            _count = 0
                            for _line in _file:
                                _count += 1
                                if '|' in _line:
                                    printx(CCFR, "可能使用了\"A|B\"形式的类型注解")
                                    printx(CCFR, "文件：%s : %d" % (_src_path, _count))
                                    return

                    os.makedirs(_dst_path.parent, exist_ok=True)
                    shutil.copyfile(_src_path, _dst_path)
                else:
                    printx("无改动：%s" % str(_src))
        else:
            printx(CCFR, "源不存在：%s" % _src_path)

    printx("\n")
    printx("生成完成")

    return 0

def link(args):

    blender_addon_dir = Path(args.blender_addon_dir).resolve()
    if not blender_addon_dir.exists():
        os.makedirs(blender_addon_dir, exist_ok=True)

    dst = blender_addon_dir.joinpath(addon_name)

    if os.path.lexists(dst):
        printx("删除旧链接")
        os.unlink(dst)

    src = prj_dir.joinpath('xdebug' if args.config == 'debug' else 'xrelease')

    p = subprocess.Popen([
        'mklink', '/d', '/h', '/j', dst, src,
    ], shell=True)
    p.communicate()
    p.wait()

    pass

def run(args):

    os.environ['ENHANCE_WINDOWS_IME'] = "YES"

    blender_dir = Path(args.blender_dir)

    exe_path = blender_dir.joinpath('Blender.exe')

    if not exe_path.exists():
        printx("找不到：", exe_path)
        return

    version: tuple[int, int, int] = None
    _rs = os.popen(f'"{exe_path}" -v')
    if _match := re.match(r'Blender (\d+).(\d+).(\d+)', _rs.readline()):
        version = (int(_match[1]), int(_match[2]), int(_match[3]))
    else:
        printx(_err := "无法获取版本信息")
        raise Exception(_err)

    blender_user_dir: Path = None
    if args.blender_user_dir:
        blender_user_dir = Path(args.blender_user_dir).resolve()
        if not blender_user_dir.exists():
            os.makedirs(blender_user_dir, exist_ok=True)
        _config = blender_user_dir.joinpath('config')
        if not _config.exists():
            os.makedirs(_config, exist_ok=True)
        _datafiles = blender_user_dir.joinpath('datafiles')
        _scripts = blender_user_dir.joinpath('scripts')
        if version >= (3, 4, 0):
            os.environ['BLENDER_USER_RESOURCES'] = str(blender_user_dir).replace('\\', '/')
            os.environ['BLENDER_SYSTEM_RESOURCES'] = str(blender_user_dir).replace('\\', '/')
        else:
            os.environ['BLENDER_USER_CONFIG'] = str(_config).replace('\\', '/')
            os.environ['BLENDER_USER_DATAFILES'] = str(_datafiles).replace('\\', '/')
            os.environ['BLENDER_USER_SCRIPTS'] = str(_scripts).replace('\\', '/')

    if args.use_wt:
        cmd = ['wt', exe_path]
    else:
        cmd = [exe_path]
    subprocess.Popen(cmd, cwd=blender_dir)

def clean(args):
    if (_dir := prj_dir.joinpath('xbuild')).exists():
        printx("删除：%s" % _dir)
        shutil.rmtree(_dir)

    if (_dir := prj_dir.joinpath('xdebug')).exists():
        printx("删除：%s" % _dir)
        shutil.rmtree(_dir)

    if (_dir := prj_dir.joinpath('xrelease')).exists():
        printx("删除：%s" % _dir)
        shutil.rmtree(_dir)

    pass

def pack(args):
    dir = prj_dir.joinpath('xrelease')

    if not dir.exists():
        printx("目录不存在：", dir)
        return
    else:
        printx("打包目录：", dir)

    try:

        import zipfile

        file = open(str(dir.joinpath('__init__.py')), 'r', encoding='utf-8')
        file_content = file.read()
        file.close()

        match = re.search(r"'version'\s*:\s*\((\d+),\s*(\d+),\s*(\d+)\)", file_content, re.I)
        if not match:
            raise TypeError("无法从 __init__.py 中读取版本信息")

        version = f"{match.group(1)}.{match.group(2)}.{match.group(3)}"

        file_name = f'{addon_full_name}_v{version}.zip'

        if (file_path := prj_dir.joinpath(file_name)).exists():
            os.remove(file_path)

        with zipfile.ZipFile(file_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(dir, arcname=addon_name)
            for _dir, dirs, files in os.walk(dir):
                if os.path.basename(_dir) == '__pycache__':
                    continue
                for file in files:
                    if file == f'_{addon_name}.dll':
                        continue
                    zipf.write(
                        fp := os.path.join(_dir, file),
                        arcname=addon_name + '/' + os.path.relpath(fp, dir)
                    )

        printx("打包完成：", file_path)

    except:
        traceback.print_exc()
        printx("打包失败")


if __name__ == '__main__':
    make()
