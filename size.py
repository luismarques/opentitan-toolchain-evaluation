#!/usr/bin/env python3

import argparse
from dataclasses import dataclass, field
from elftools.elf.elffile import ELFFile
from elftools.elf.segments import Segment
import glob
from pathlib import Path
import subprocess

base1 = 'opentitan/build-out'
base2 = 'opentitan2/build-out'

def alt_path(f):
    return str(base2 / Path(*Path(f).parts[2:]))

@dataclass(order=True)
class SizeComparison:
    sort_index: int = field(init=False)
    file1: str
    file2: str
    text1_size: int
    text2_size: int

    def __post_init__(self):
        self.sort_index = self.size_rel_delta()

    def size_abs_delta(self):
        return self.text2_size - self.text1_size

    def size_rel_delta(self):
        if self.text1_size == 0:
            return 0
        return ((self.text2_size - self.text1_size) / self.text1_size)

def obj_files(ext = 'elf'):
    for f in glob.glob(f'{base1}/**/*.{ext}', recursive=True):
        yield (f, alt_path(f))

def elf_text_size(file_name, include_rodata = True):
    text_size = 0
    rodata_size = 0
    with open(file_name, 'rb') as elf_file:
        for section in ELFFile(elf_file).iter_sections():
            if section.name == '.text':
                text_size = text_size + section.data_size
            elif section.name == '.rodata':
                rodata_size = rodata_size + section.data_size
    if include_rodata:
        return text_size + rodata_size
    else:
        return text_size

def bin_size(file_name):
    return Path(file_name).stat().st_size

def compare_elfs():
    sizes = []
    for f1, f2 in obj_files():
        t1 = elf_text_size(f1)
        t2 = elf_text_size(f2)
        sc = SizeComparison(f1, f2, t1, t2)
        sizes.append(sc)
    sizes.sort()
    for size in sizes:
        print(f'{size.size_rel_delta():.2%} {size.size_abs_delta()} {size.file1}')

def compare_bins():
    sizes = []
    for f1, f2 in obj_files('bin'):
        t1 = bin_size(f1)
        t2 = bin_size(f2)
        sc = SizeComparison(f1, f2, t1, t2)
        sizes.append(sc)
    sizes.sort()
    for size in sizes:
        print(f'{size.size_rel_delta():.2%} {size.size_abs_delta()} {size.file1}')

def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--bins', action='store_true', help='Analyze binary files')
    arg_parser.add_argument('file', nargs='?', help='Analyze function sizes in ELF file')
    options = arg_parser.parse_args()
    if options.file:
        compare_functions(options.file)
        return
    if options.bins:
        compare_bins()
    else:
        compare_elfs()

def compare_functions(file_name):
    elf_file1 = open(file_name, 'rb')
    elf_file2 = open(alt_path(file_name), 'rb')
    elf1 = ELFFile(elf_file1)
    elf2 = ELFFile(elf_file2)
    symtab1 = elf1.get_section_by_name('.symtab')
    symtab2 = elf2.get_section_by_name('.symtab')
    total = 0
    for sym1 in symtab1.iter_symbols():
        info = sym1['st_info']
        type = info['type']
        if type == 'STT_FUNC' or type == 'STT_OBJECT':
            size1 = sym1['st_size']
            syms2 = symtab2.get_symbol_by_name(sym1.name)
            if syms2 is not None:
                assert len(syms2) >= 1
                sym2 = syms2[0]
                size2 = sym2['st_size']
            else:
                size2 = 0
            rel_size = size2 - size1
            total = total + rel_size
            if size1 != size2:
                print(f'{rel_size:+4} {size1:4} {size2:4} {sym1.name:40} {file_name}')
    print(f'={total}')

if __name__ == '__main__':
    main()
