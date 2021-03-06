import sys
import shutil

from .config import VERSION
from .core import SingleTaskExecutor, CmdTaskWorker


PADDING = 4


def color_line(line, color_number):
    result = ''
    if color_number >= 8:
        result += "\033[1m"
        color_number -= 8
    result += f"\033[03{color_number}m{line}"
    # reset font:
    result += "\033[0m"
    return result


def bold_line(line):
    return f'\033[1m{line}\033[0m'


def get_term_width():
    return shutil.get_terminal_size((80, 80)).columns


def format_paragraph(line):
    term_width = get_term_width()
    max_line_width = term_width - PADDING * 2

    result = []
    current_line = []
    line_length = 0
    for word in line.split():
        if len(word) + line_length > max_line_width:
            result.append(current_line)
            current_line = []
            line_length = 0
        current_line.append(word)
        line_length += len(word) + 1
    result.append(current_line)

    return '\n'.join([
        ' '.join(
            [(PADDING-1)*' ', ] +
            words +
            [(PADDING-1)*' ', ],
        )
        for words in result
    ])


def print_not_found_packages(not_found_packages):
    print("{} {}".format(
        color_line(':: warning:', 11),
        bold_line('Following packages can not be found in AUR:'),
    ))
    for package in not_found_packages:
        print(format_paragraph(package))


def pretty_print_upgradeable(packages_updates, verbose=False):

    def get_common_string(str1, str2):
        result = ''
        if '' in (str1, str2):
            return result
        counter = 0
        while (
                counter < len(str1)
        ) and (
            counter < len(str2)
        ) and (
            str1[counter] == str2[counter]
        ):
            result += str1[counter]
            counter += 1
        return result

    def get_version_diff(version, common_version):
        new_version_postfix = version
        if common_version != '':
            _new_version_postfix = version.split(
                common_version
            )[1:]
            new_version_postfix = common_version.join(_new_version_postfix)
        return new_version_postfix

    def pretty_format(pkg_update):
        common_version = get_common_string(
            pkg_update.Current_Version, pkg_update.New_Version
        )
        version_color = 10
        old_color = 11
        new_color = 9
        column_width = min(int(get_term_width() / 2), 45)
        sort_by = '{:03d}{}'.format(
            len(common_version)*10+len(pkg_update.New_Version),
            pkg_update.Name
        )
        return ' {:<{width}} {:<{width2}} -> {}{}{verbose}'.format(
            bold_line(pkg_update.Name),
            color_line(common_version, version_color) +
            color_line(
                get_version_diff(pkg_update.Current_Version, common_version),
                old_color
            ),
            color_line(common_version, version_color),
            color_line(
                get_version_diff(pkg_update.New_Version, common_version),
                new_color
            ),
            width=column_width,
            width2=column_width - 3,
            verbose=(
                '' if not (verbose and pkg_update.Description)
                else f'\n{format_paragraph(pkg_update.Description)}'
            )
        ), sort_by

    print(
        '\n'.join([
            f'{line}' for line, _ in sorted(
                [
                    pretty_format(pkg_update)
                    for pkg_update in packages_updates
                ],
                key=lambda x: x[1],
            )
        ])
    )


def print_upgradeable(packages_updates):
    print('\n'.join([
        pkg_update.Name
        for pkg_update in packages_updates
    ]))


def print_sysupgrade(
        repo_packages_updates=None, aur_updates=None, new_aur_deps=None, verbose=False
):
    if repo_packages_updates:
        print('\n{} {}'.format(
            color_line('::', 12),
            bold_line('Repository package{plural} will be installed:'.format(
                plural='s' if len(repo_packages_updates) > 1 else ''
            ))
        ))
        pretty_print_upgradeable(
            repo_packages_updates, verbose=verbose
        )
    if aur_updates:
        print('\n{} {}'.format(
            color_line('::', 14),
            bold_line('AUR package{plural} will be installed:'.format(
                plural='s' if len(aur_updates) > 1 else ''
            ))
        ))
        pretty_print_upgradeable(
            aur_updates, verbose=verbose
        )
    if new_aur_deps:
        print('\n{} {}'.format(
            color_line('::', 11),
            bold_line('New dependenc{plural} will be installed from AUR:'.format(
                plural='ies' if len(new_aur_deps) > 1 else 'y'
            ))
        ))
        pretty_print_upgradeable(
            new_aur_deps, verbose=verbose
        )

    print()
    answer = input('{} {}\n{} {}\n> '.format(
        color_line('::', 12),
        bold_line('Proceed with installation? [Y/n] '),
        color_line('::', 12),
        bold_line('[v]iew package detail   [m]anually select packages')
    ))
    return answer


def print_version():
    pacman_version = SingleTaskExecutor(CmdTaskWorker(
        ['pacman', '--version', ],
    )).execute().stdout.splitlines()[1].strip(' .-')
    sys.stdout.buffer.write((r"""
      /:}               _
     /--1             / :}
    /   |           / `-/
   |  ,  --------  /   /
   |'                 Y      Pikaur """+VERSION+r"""
  /                   l      (C) 2018 Pikaur development team
  l  /       \        l      Licensed under GPLv3
  j  ●   .   ●        l
 { )  ._,.__,   , -.  {      """+pacman_version+r"""
  У    \  _/     ._/   \

""").encode())


class ProgressBar(object):

    message = None
    print_ratio = None
    index = 0
    progress = 0

    def __init__(self, message, length):
        self.message = message
        width = get_term_width() - len(message)
        self.print_ratio = length / width
        print(message, end='')

    def update(self):
        self.index += 1
        if self.index / self.print_ratio > self.progress:
            self.progress += 1
            print('.', end='')
            sys.stdout.flush()

    def __enter__(self):
        return self.update

    def __exit__(self, *exc_details):
        print()
