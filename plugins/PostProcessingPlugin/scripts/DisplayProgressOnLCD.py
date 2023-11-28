# Cura PostProcessingPlugin
# Author:   Mathias Lyngklip Kjeldgaard, Alexander Gee, Kimmo Toivanen, Inigo Martinez
# Date:     July 31, 2019
# Modified: Nov 30, 2021

# Description:  This plugin displays progress on the LCD. It can output the estimated time remaining and the completion percentage.

from ..Script import Script

import re
import datetime

class DisplayProgressOnLCD(Script):

    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name": "Display Progress On LCD",
            "key": "DisplayProgressOnLCD",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "time_remaining":
                {
                    "label": "Time Remaining",
                    "description": "Select to write remaining time to the display.Select to write remaining time on the display using M117 status line message (almost all printers) or using M73 command (Prusa and Marlin 2 if enabled).",
                    "type": "bool",
                    "default_value": false
                },
                "time_remaining_method":
                {
                    "label": "Time Reporting Method",
                    "description": "How should remaining time be shown on the display? It could use a generic message command (M117, almost all printers), or a specialised time remaining command (M73, Prusa and Marlin 2).",
                    "type": "enum",
                    "options": {
                        "m117":"M117 - All printers",
                        "m73":"M73 - Prusa, Marlin 2",
                        "m118":"M118 - Octoprint"
                    },
                    "enabled": "time_remaining",
                    "default_value": "m117"
                },
                "update_frequency":
                {
                    "label": "Update frequency",
                    "description": "Update remaining time for every layer or periodically every minute or faster.",
                    "type": "enum",
                    "options": {"0":"Every layer","15":"Every 15 seconds","30":"Every 30 seconds","60":"Every minute"},
                    "default_value": "0",
                    "enabled": "time_remaining"
                },
                "percentage":
                {
                    "label": "Percentage",
                    "description": "When enabled, set the completion bar percentage on the LCD using Marlin's M73 command.",
                    "type": "bool",
                    "default_value": false
                }
            }
        }"""

    # Get the time value from a line as a float.
    # Example line ;TIME_ELAPSED:1234.6789 or ;TIME:1337
    def getTimeValue(self, line):
        list_split = re.split(":", line)  # Split at ":" so we can get the numerical value
        return float(list_split[1])  # Convert the numerical portion to a float

    def outputTime(self, lines, line_index, time_left, mode):
        # Do some math to get the time left in seconds into the right format. (HH,MM,SS)
        time_left = max(time_left, 0)
        m, s = divmod(time_left, 60)
        h, m = divmod(m, 60)
        # Create the string
        if mode == "m117":
            current_time_string = "{:d}h{:02d}m{:02d}s".format(int(h), int(m), int(s))
            # And now insert that into the GCODE
            lines.insert(line_index, "M117 Time Left {}".format(current_time_string))
        elif mode == "m118":
            current_time_string = "{:d}h{:02d}m{:02d}s".format(int(h), int(m), int(s))
            # And now insert that into the GCODE
            lines.insert(line_index, "M118 A1 P0 action:notification Time Left {}".format(current_time_string))
        else:
            mins = int(60 * h + m + s / 30)
            lines.insert(line_index, "M73 R{}".format(mins))

    def execute(self, data):
        output_time = self.getSettingValueByKey("time_remaining")
        output_time_method = self.getSettingValueByKey("time_remaining_method")
        output_frequency = int(self.getSettingValueByKey("update_frequency"))
        output_percentage = self.getSettingValueByKey("percentage")
        line_set = {}
        if output_percentage or output_time:
            total_time = -1
            previous_layer_end_percentage = 0
            previous_layer_end_time = 0
            for layer in data:
                layer_index = data.index(layer)
                lines = layer.split("\n")

                for line in lines:
                    if (line.startswith(";TIME:") or line.startswith(";PRINT.TIME:")) and total_time == -1:
                        # This line represents the total time required to print the gcode
                        total_time = self.getTimeValue(line)
                        line_index = lines.index(line)

                        # In the beginning we may have 2 M73 lines, but it makes logic less complicated
                        if output_time:
                            self.outputTime(lines, line_index, total_time, output_time_method)

                        if output_percentage:
                            # Emit 0 percent to sure Marlin knows we are overriding the completion percentage
                            if output_time_method == "m118":
                                lines.insert(line_index, "M118 A1 P0 action:notification Data Left 0/100")
                            else:
                                lines.insert(line_index, "M73 P0")

                    elif line.startswith(";TIME_ELAPSED:"):
                        # We've found one of the time elapsed values which are added at the end of layers
                        
                        # If we have seen this line before then skip processing it. We can see lines multiple times because we are adding
                        # intermediate percentages before the line being processed. This can cause the current line to shift back and be
                        # encountered more than once
                        if line in line_set:
                            continue
                        line_set[line] = True

                        # If total_time was not already found then noop
                        if total_time == -1:
                            continue

                        current_time = self.getTimeValue(line)
                        line_index = lines.index(line)
                        
                        if output_time:
                            if output_frequency == 0:
                                # Here we calculate remaining time
                                self.outputTime(lines, line_index, total_time - current_time, output_time_method)
                            else:
                                # Here we calculate remaining time and how many outputs are expected for the layer
                                layer_time_delta = int(current_time - previous_layer_end_time)
                                layer_step_delta = int((current_time - previous_layer_end_time) / output_frequency)
                                # If this layer represents less than 1 step then we don't need to emit anything, continue to the next layer
                                if layer_step_delta != 0:
                                    # Grab the index of the current line and figure out how many lines represent one second
                                    step = line_index / layer_time_delta
                                    # Move new lines further as we add new lines above it
                                    lines_added = 1
                                    # Run through layer in seconds
                                    for seconds in range(1, layer_time_delta + 1):
                                        # Time from start to decide when to update
                                        line_time = int(previous_layer_end_time + seconds)
                                        # Output every X seconds and after last layer
                                        if line_time % output_frequency == 0 or line_time == total_time:
                                            # Line to add the output
                                            time_line_index = int((seconds * step) + lines_added)

                                            # Insert remaining time into the GCODE
                                            self.outputTime(lines, time_line_index, total_time - line_time, output_time_method)
                                            # Next line will be again lower
                                            lines_added = lines_added + 1

                                    previous_layer_end_time = int(current_time)

                        if output_percentage:
                            # Calculate percentage value this layer ends at
                            layer_end_percentage = int((current_time / total_time) * 100)

                            # Figure out how many percent of the total time is spent in this layer
                            layer_percentage_delta = layer_end_percentage - previous_layer_end_percentage
                            
                            # If this layer represents less than 1 percent then we don't need to emit anything, continue to the next layer
                            if layer_percentage_delta != 0:
                                # Grab the index of the current line and figure out how many lines represent one percent
                                step = line_index / layer_percentage_delta

                                for percentage in range(1, layer_percentage_delta + 1):
                                    # We add the percentage value here as while processing prior lines we will have inserted
                                    # percentage lines before the current one. Failing to do this will upset the spacing
                                    percentage_line_index = int((percentage * step) + percentage)

                                    # Due to integer truncation of the total time value in the gcode the percentage we 
                                    # calculate may slightly exceed 100, as that is not valid we cap the value here
                                    output = min(percentage + previous_layer_end_percentage, 100)
                                    
                                    # Now insert the sanitized percentage into the GCODE
                                    if output_time_method == "m118":
                                        lines.insert(percentage_line_index, "M118 A1 P0 action:notification Data Left {}/100".format(output))
                                    else:
                                        lines.insert(percentage_line_index, "M73 P{}".format(output))

                                previous_layer_end_percentage = layer_end_percentage

                # Join up the lines for this layer again and store them in the data array
                data[layer_index] = "\n".join(lines)
        return data
