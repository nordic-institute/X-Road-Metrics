#The MIT License
#Copyright (c) 2021- Nordic Institute for Interoperability Solutions (NIIS)
#Copyright (c) 2017-2020 Estonian Information System Authority (RIA)
#
#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in
#all copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#THE SOFTWARE.

library("yaml")

args <- commandArgs(trailingOnly = TRUE)
profile.suffix <- ""

if (length(args) >= 2 && args[1] == "--profile") {
  profile.suffix <- paste0("_", args[2])
}

settings_file_name <- paste0("settings", profile.suffix, ".yaml")

#try cwd first, then the default location for settings
if (file.exists(paste0("./", settings_file_name))) {
  settings <- yaml.load_file(paste0("./", settings_file_name));
} else {
  settings <- yaml.load_file(paste0("/etc/xroad-metrics/networking/", settings_file_name))
}

#postgres doesn't like uppercase or dashes
settings$postgres$suffix <- tolower(gsub("-", "_",settings$xroad$instance))

logfile <- paste0(settings$logger$"log-path", "/prepare_data_log.json")
heartbeatfile <- paste0(settings$logger$"heartbeat-path", "/prepare_data_heartbeat.json")
