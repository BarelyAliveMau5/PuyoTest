#!/usr/bin/env python3

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
from typing import List, Tuple, Any
from array import array

zf = '.'  # zero fill, empty area, empty space
big_group = 4  # minimum group size to be considered big enough to get removed

types = "abcde"  # more types -> greater complexity -> harder to solve

sz_x = 6  # arena width
sz_y = 12  # arena height

arena: List[int] = []


class Board:
    zf = 0
    # todo: implement all board functions

    def __init__(self, width: int, height: int, variations: int=5):
        self._field: array = array('B', bytes([Board.zf] * width * height))
        self._width = width
        self._height = height
        self._variations = variations

    def resize(self, new_width, new_height):
        self._field.fromlist([Board.zf for _ in range(new_width * new_height)])

    def __iter__(self):
        for y in range(self._height):
            for x in range(self._width):
                yield x, y

    def at(self, x, y):
        return self._field[x + y * self._width]

    def pulldown(self):
        for x in range(self._width):
            # select only non-empty-space (non-zfs)
            y_list = [self.at(x, y) for y in range(self._height)
                      if self.at(x, y) != Board.zf]
            # fill space "above" with empty-space, acts like gravity
            y_list = [zf for _ in range(sz_y - len(y_list))] + y_list
            # apply modifications
            for y, v in enumerate(y_list):
                set_at(x, y, v)


# todo: implement game solver
# todo: remove old code thats not inside classes

def create_arena():
    global arena
    arena = [zf for _ in range(sz_x * sz_y)]


create_arena()


# translate 2d to 1d
def at(x: int, y: int):
    return arena[x + y * sz_x]


def set_at(x: int, y: int, v: Any):
    arena[x + y * sz_x] = v


# store messages to print later
msgs: List[str] = []


def s_print(*nargs, end='\n', sep=' '):
    msgs.append(sep.join(map(str, nargs)) + end)


def arena_iter() -> Tuple[int, int]:
    for y in range(sz_y):
        for x in range(sz_x):
            yield x, y


def pull_down():
    # columns don't mess with side neighbors
    for x in range(sz_x):
        # select only non-empty-space (non-zfs)
        y_list = [at(x, y) for y in range(sz_y) if at(x, y) != zf]
        # fill space "above" with empty-space, acts like gravity
        y_list = [zf for _ in range(sz_y - len(y_list))] + y_list
        # apply modifications
        for y, v in enumerate(y_list):
            set_at(x, y, v)


def __get_groups(x: int, y: int, groups):
    if not (sz_x > x >= 0 and sz_y > y >= 0):  # boundary error checking
        # this should never be true
        return
    group_type = at(x, y)
    if group_type == zf:  # ignore empty space
        return

    neighbors: List[Tuple[int, int]] = []

    point_queue: List[Tuple[int, int]] = [(x, y)]
    # based on rosetta code's c++ flood-fill algorithm
    while point_queue:
        px, py = point_queue.pop(0)
        if sz_x > px >= 0 and sz_y > py >= 0:  # boundary checking
            if at(px, py) == group_type and (px, py) not in neighbors:
                neighbors.append((px, py))
                # next neighbors to search
                point_queue.append((px + 1, py))
                point_queue.append((px - 1, py))
                point_queue.append((px, py + 1))
                point_queue.append((px, py - 1))
    groups.extend([neighbors])
    return


def find_groups(debug=False):
    groups: List[Tuple[int, int]] = []  # [ [(x, y), (x, y)], ...]
    for x, y in arena_iter():
        # avoid processing known groups
        if not [i for i in groups if (x, y) in i]:
            __get_groups(x, y, groups)

    if debug:
        for i in groups:
            x, y = i[0]
            print("type =", at(x, y), " points:", i)
    return groups


def has_big_groups(min_=big_group):
    groups = find_groups()
    for points in groups:
        if len(points) >= min_:
            return True


def remove_big_groups(min_=big_group):
    groups = find_groups()
    for points in groups:
        if len(points) >= min_:
            for x, y in points:
                set_at(x, y, zf)


def show():
    for y in range(sz_y):
        for x in range(sz_x):
            s_print(at(x, y), end='')
        s_print("")
    population = len([0 for x, y in arena_iter() if at(x, y) != zf])
    s_print("population:", population, "\n")
    return population


def iter_game():
    step = 0
    pop = sz_x * sz_y
    while has_big_groups():
        s_print("step:", step)
        remove_big_groups()
        show()
        pull_down()
        pop = show()
        step += 1
    return step, pop


def main(max_pop):
    # Brute-force way to find chains that finish with max_pop defined below.
    # Quite slow because of some obvious factors like... python itself? and
    # the fact that i didn't optimize the code for performance. its a TEST
    from random import randint
    i = 0
    smallest = sz_x * sz_y
    while True:
        msgs.clear()
        for x, y in arena_iter():
            # randint seems a lot faster than random.choice
            set_at(x, y, types[randint(1, len(types) - 1)])
        show()
        step, pop = iter_game()
        s_print("total steps:", step)
        if pop < max_pop:
            print()
            break
        smallest = min(smallest, pop)
        # i like to see how far we are
        print("\rsimulation: ", i, "smallest:", smallest, end='')
        i += 1
    print(*msgs, sep='')


def simulate(values):
    # mainly useful to test manually-created chains
    # input must be a sequence of values representing the value of each cell
    # if the value is not mapped (in the values dict) it will be shown as a '?'
    global arena
    if len(values) != 72:
        return
    arena = list(values)
    msgs.clear()
    show()
    iter_game()
    print(*msgs, sep='')


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
    parser.add_argument("-z", help="empty space character(s)", default=".",
                        metavar="CHARS", action="store")
    parser.add_argument("-x", help="define the characters of the random set",
                        metavar="CHARS", action="store")
    parser.add_argument("-d", help="arena dimension", metavar=("X", "Y"),
                        action="store", nargs=2, type=int)
    return parser


if __name__ == "__main__":
    args = argument_parser().parse_args()
    if args.x and args.c:
        print("Option -x cannot be used with -c")
        exit(-1)
    elif args.x:
        types = args.x
    if args.z:
        zf = args.z
    if args.d:
        sz_x, sz_y = args.d
        create_arena()
    if args.c:
        if len(args.c) != sz_x * sz_y:
            print(f"custom sets must be {sz_x * sz_y} characters long.")
            exit(-1)
        simulate(args.c)
    elif args.s:
        main(args.s)
    else:
        main(25)
