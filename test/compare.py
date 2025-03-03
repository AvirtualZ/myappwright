from utils import logutils

f1_list = logutils.get_list_from_file('未使用IP 379.txt')
f2_list = logutils.get_list_from_file('总汇928.txt', f1_list)

logutils.save_list_to_file('output.txt', f2_list)