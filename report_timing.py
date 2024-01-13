import re
from prettytable import PrettyTable

file_name = "./Timing.rpt"

# Mở tệp tin gzip bằng gzcat
with open(file_name, "r") as file:
    data = file.read()

# Chia dòng
lines = data.split("\n")

# Khai báo biến để lưu kết quả
lines_containing_slack_time = []
lines_end_point  = []
lines_start_point  = []
lines_path_type=[]
# Sử dụng vòng lặp để lặp qua từng dòng
find_end_point  = 0
for line in lines:
    # Kiểm tra xem từ khóa "slack time" có xuất hiện trong dòng hay không
    if re.search("VIOLATED", line):
        # Lưu dòng chứa từ khóa "slack time" vào biến mới
        lines_containing_slack_time.append(line)
    elif re.search("Endpoint", line):
        if find_end_point == 0:
            find_end_point = 1
        lines_end_point .append(line)
    elif re.search("Startpoint", line):
        lines_start_point .append(line)
    elif re.search("Path Type", line):
        lines_path_type .append(line)
# Sử dụng biến lưu kết quả sau này
num_line = min(len(lines_containing_slack_time), len(lines_end_point ), len(lines_start_point ),len(lines_path_type))
# Tạo đối tượng PrettyTable
table = PrettyTable()
table.field_names = ["Slack", "End Point", "Startpoint","Path type"]

for i in range(num_line):
    slack_line = lines_containing_slack_time[i]
    end_point_line = lines_end_point [i]
    start_point_line = lines_start_point [i]
    path_type_line =lines_path_type [i]
    # Thêm dữ liệu vào bảng
    table.add_row([slack_line, end_point_line, start_point_line,path_type_line])

# In bảng ra màn hình
print(table)
