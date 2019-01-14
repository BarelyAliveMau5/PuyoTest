#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This is a prototype/test/playground/toy project i've created out of curiosity
# to discover how to create a game like puyo-puyo, and also see how difficult
# it would be to create a super nice chain in the game. This was not supposed to
# be a pretty copy of my work. This is literally just a bunch of code i wrote to
# test stuff.
# I really want to implement a monte carlo search algorithm to generate
# efficient chains, instead of this crappy brute-force code implemented right
# now and i eventually will when i finish my college stuff. I dont plan to
# implement it using python in the future though (*cough* slow af *cough*).
# Maybe using the beloved Godot Engine? who knows :)

import logging
from array import array
from typing import List, Tuple

logging.basicConfig(
    format='%(asctime)s %(funcName)s %(levelname)s: %(message)s',
    datefmt="%Y-%m-%d %H:%M:%S"
)

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class Board:
    zf = 0  # zero fill, empty space
    brick = 255  # does not chain by itself
    print_zf = '.'
    print_brick = "#"
    types = "abcde"
    big_group = 4

    def __init__(self, width=6, height=12):
        """
        creates a new board

        :param width:
        :param height:
        """
        self._variations = len(self.types)
        if self._variations > 26:
            log.error("cannot have more than 26 variations")
            return
        self._field: array = array('B', bytes([self.zf] * width * height))
        self._width = width
        self._height = height
        self._char_dict = self._make_char_dict()
        log.debug(f"created board: w:{width} h:{height} "
                  f"types:{self._variations}")

    def _make_char_dict(self):
        chars = {i + 1: self.types[i] for i in range(self._variations)}
        chars[0] = self.print_zf
        chars[255] = self.print_brick
        return chars

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    def resize(self, new_w, new_h, keep_old_data=False):
        old = array("B", self._field) if keep_old_data else None
        self._field = array('B', bytes([self.zf] * new_w * new_h))
        log.debug(f"resized: {self.width}x{self.height} -> {new_w}x{new_h}")
        if keep_old_data:
            for x, y in self:
                index = x + y * self._width  # it still uses the old width
                self._field[index] = old[index]
            log.debug(f"loaded old data. ({self.width * self.height} bytes)")
        self._width, self._height = new_w, new_h

    def __iter__(self):
        for y in range(self._height):
            for x in range(self._width):
                yield x, y

    def at(self, x, y):
        return self._field[x + y * self._width]

    def set_at(self, x, y, v):
        self._field[x + y * self._width] = v

    def load_str(self, string):
        """
        sets all the board values with this string
        :param string:
        :return:
        """
        # i guess it doesnt works if print_zf has more than 1 char
        if sum(1 for i in string if i not in
               self.types + self.print_zf + self.print_brick):
            log.error(f"undefined type")
            return
        inv_char_dict = {char: i for i, char in self._char_dict.items()}
        for i, v in enumerate(string):
            self._field[i] = inv_char_dict[v]
        log.debug(f"loaded string: {string}")

    def pulldown(self):
        for x in range(self._width):
            # select only non-empty-space (non-zfs)
            col = [self.at(x, y) for y in range(self._height)
                   if self.at(x, y) != self.zf]

            # fill space "above" with empty-space, acts like gravity
            col = [self.zf for _ in range(self._height - len(col))] + col
            for y, v in enumerate(col):
                self.set_at(x, y, v)

    @staticmethod
    def pair(v1: int, v2: int, vertical=False) -> List[List[int]]:
        if vertical:
            return [[v1, Board.zf], [v2, Board.zf]]
        return [[v1, v2], [Board.zf, Board.zf]]

    def add_pair(self, pos: int, values: List[List[int]]):
        # todo: test add_pair
        """
        adds a pair onto the board
        values it must be a 2x2 matrix filled with zf and the types
        eg: [[1,0],
             [2,0]]
        :param pos:
        :param values: 2d iterable with types inside
        :return:
        """
        # p0 px
        # py
        # its always either a vertical or horizontal pair
        p0, px, py = values[0][0], values[1][0], values[0][1]
        if p0 == self.zf or (px != self.zf and py != self.zf) or values[1][1]:
            log.error("invalid pair")
            return

        # avoid index out of bounds
        pos = self._width - 1 if pos >= self._width else pos
        if px != self.zf and pos == self._width - 1:
            pos -= 1
            log.warning(f"using position {pos}")
        if self.at(pos, 0) != self.zf or self.at(pos + 1, 0) != self.zf \
                or self.at(pos, 1) != self.zf:
            log.error(f"cannot add pair at {pos}. cell occupied")

        self.set_at(pos, 0, p0)
        if px != self.zf:
            self.set_at(pos + 1, 0, px)
        else:
            self.set_at(pos, 1, py)
        self.pulldown()

    def __get_group(self, x: int, y: int, groups):
        if not (self._width > x >= 0 and self._height > y >= 0):
            log.error("index out of bounds")
            return
        group_type = self.at(x, y)
        if group_type == self.zf or group_type == self.brick:
            return

        neighbors: List[Tuple[int, int]] = []

        point_queue: List[Tuple[int, int]] = [(x, y)]
        # based on rosetta code's c++ flood-fill algorithm
        while point_queue:
            px, py = point_queue.pop(0)
            if self._width > px >= 0 and self._height > py >= 0:
                value_at = self.at(px, py)
                if value_at == self.brick:
                    neighbors.append((px, py))
                    continue
                if value_at == group_type:
                    if (px, py) not in neighbors:
                        neighbors.append((px, py))
                        # next neighbors to search
                        point_queue.append((px + 1, py))
                        point_queue.append((px - 1, py))
                        point_queue.append((px, py + 1))
                        point_queue.append((px, py - 1))
        groups.extend([neighbors])
        return

    def _find_groups(self):
        groups: List[Tuple[int, int]] = []  # [ [(x, y), (x, y)], ...]
        for x, y in self:
            # avoid processing known groups
            if not [i for i in groups if (x, y) in i]:
                self.__get_group(x, y, groups)
        return groups

    def _has_big_groups(self, min_=big_group):
        groups = self._find_groups()
        for points in groups:
            # dont count bricks
            if len([(x, y) for x, y in points
                    if self.at(x, y) != self.brick]) >= min_:
                return True

    def _remove_big_groups(self, min_=big_group):
        groups = self._find_groups()
        for points in groups:
            # dont count bricks
            if len([(x, y) for x, y in points
                    if self.at(x, y) != self.brick]) >= min_:
                for x, y in points:
                    self.set_at(x, y, self.zf)

    def population(self):
        return sum(1 for x, y in self if self.at(x, y) != self.zf)

    def step(self, pulldown=True):
        self._remove_big_groups()
        if pulldown:
            self.pulldown()

    def solve(self):
        while self._has_big_groups():
            self.step()

    def show(self):
        for x, y in self:
            print(self._char_dict[self.at(x, y)],
                  end='\n' if x == self._width - 1 else '')


def argument_parser():
    import argparse
    import textwrap
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent('''\
        note:
            custom sets are case-sensitive and must be X*Y characters long 
            when redefined with -d (default is 72, 6x12). 
            emojis can be used too if you like them (needs UTF-8 support)

        example:
            custom set:
            run.py -c cbdeabdccabebbcbbcbdbbbdaaecceaeaaebadcdedbbdeabbadcd\
deaecccdaeaaecdeaee

            custom set with emoji:
            run.py -z ".." -c 🍰👀😈😡😀👀😈🍰🍰😀👀😡👀👀🍰👀👀🍰👀😈👀👀👀😈😀😀😡🍰🍰😡😀😡😀😀😡👀😀😈🍰😈😡😈👀👀😈😡\
😀👀👀😀😈🍰😈😈😡😀😡🍰🍰🍰😈😀😡😀😀😡🍰😈😡😀😡😡
             '''))

    group = parser.add_mutually_exclusive_group()
    group.add_argument("-c", help="simulate a custom set. Implies -s.",
                       metavar="SET", action='store')
    group.add_argument("-s",
                       help="simulate random sets until population reaches N",
                       metavar="N", action="store", type=int,
                       choices=range(1, 72))
    parser.add_argument("-z", help="empty space character(s)",
                        metavar="CHARS", action="store")
    parser.add_argument("-b", help="brick character",
                        metavar="CHAR", action="store")
    parser.add_argument("-x", help="define variations of the random set",
                        metavar="CHARS", action="store", type=int)
    parser.add_argument("-d", help="arena dimension", metavar=("X", "Y"),
                        action="store", nargs=2, type=int)
    return parser


# todo: implement gameplay class
# todo: implement ai
# todo: implement interactive inputs via commands


if __name__ == "__main__":
    cmd_args = argument_parser().parse_args()
    board = Board()

    if cmd_args.x and cmd_args.c:
        print("Option -x cannot be used with -c")
        exit(-1)

    if cmd_args.x:  # define the characters of the random set
        Board.types = cmd_args.x
        board = Board()

    if cmd_args.z:  # empty space character(s)
        if sum(1 for i in cmd_args.z if i in board.types):
            log.error("character reserved for printing")
            exit(-1)
        Board.print_zf = cmd_args.z

    if cmd_args.b:
        if cmd_args.b in Board.types or cmd_args.b in board.print_zf:
            log.error("character reserved for printing")
            exit(-1)
        Board.print_brick = cmd_args.b

    if cmd_args.d:  # arena dimension
        board = Board(*cmd_args.d)

    if cmd_args.c:  # simulate a custom set
        size = board.width * board.height
        if len(cmd_args.c) != size:
            print(f"custom sets must be {size} characters long.")
            exit(-1)
        types = sorted("".join(set(cmd_args.c)))
        if types != sorted(board.types):
            Board.print_zf = board.print_zf
            Board.types = "".join(types)
            board = Board(board.width, board.height)
        board.load_str(cmd_args.c)
        board.solve()
        board.show()
    elif cmd_args.s:
        print("simulations are disabled right now.")
        exit(-1)
        while board.population() > cmd_args.s:
            # todo: implement simulations
            break
    else:
        pass
