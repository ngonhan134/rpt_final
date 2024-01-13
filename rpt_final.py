import re
from prettytable import PrettyTable
import sys


# Check if the correct number of command-line arguments is provided
if len(sys.argv) != 2:
    print("Usage: python rpt_final.py <file_path>")
    sys.exit(1)

# Extract the file path from the command-line arguments
file_name = sys.argv[1]

# Open the gzip file using gzcat
with open(file_name, "r") as file:
    data = file.read()

# Split the data into lines
lines = data.split("\n")

# Declare variables to store results
lines_containing_slack_time = []
lines_end_point = []
lines_start_point = []
lines_path_type = []
lines_path_group =[]
# Use a loop to iterate over each line
find_end_point = 0
for line in lines:
    # Check if the keyword "VIOLATED" appears in the line
    if re.search("slack", line):
        # Save the last column of the line containing the keyword "VIOLATED"
        #lines_containing_slack_time.append(re.split(r'\s+', line.strip())[-1])
        lines_containing_slack_time.append(line)
    elif re.search("Endpoint", line):
        if find_end_point == 0:
            find_end_point = 1
        lines_end_point.append(re.split(r'\s+', line.strip())[-1])
        #lines_end_point .append(line)
    elif re.search("Startpoint", line):
        lines_start_point.append(re.split(r'\s+', line.strip())[-1])
       #lines_start_point.append(line)
    elif re.search("Path Type", line):
        lines_path_type.append(re.split(r'\s+', line.strip())[-1])
        #lines_path_type.append(line)
    elif re.search("Path Group", line):
        lines_path_group.append(re.split(r'\s+', line.strip())[-1])
        #lines_path_group.append(line)

# Use the minimum length of the result lists for iteration
num_line = min(len(lines_containing_slack_time), len(lines_end_point), len(lines_start_point), len(lines_path_type),len(lines_path_group))

# Create a PrettyTable object
table = PrettyTable()
table.field_names = ["Index","Slack","Start point", "End Point",  "Path type","Path group"]
#table.field_names = ["Index", "Slack", "End Point", "Startpoint", "Path type"]

# Add data to the table
for i in range(num_line):
    slack_line = lines_containing_slack_time[i]
    end_point_line = lines_end_point[i]
    start_point_line = lines_start_point[i]
    path_type_line = lines_path_type[i]
    path_group_line=lines_path_group[i]

    table.add_row([i+1,slack_line,start_point_line, end_point_line, path_type_line,path_group_line])
    #table.add_row([i + 1, slack_line, end_point_line, start_point_line, path_type_line])


# Print the table to the screen
print(table)
