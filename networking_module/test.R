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

save.image('test.RData')

library(dplyr)
library(jsonlite)

membernames<-flatten(fromJSON(file('riha_EE.json'))) %>% distinct(member_code, member_name)
dat<-readRDS("/srv/shiny-server/EE/dat.rds")

dat.membercodes<-union(unique(dat$clientmembercode), unique(dat$servicemembercode))
length(dat.membercodes) #205

length(unique(membernames$member_code)) #238

dat.membercodes %in% unique(membernames$member_code)

data.frame(
  dat.membercodes=dat.membercodes,
  present.in.riha=dat.membercodes %in% unique(membernames$member_code)
) %>% filter(present.in.riha==F)

membernames %>% filter(member_code %in% {membernames %>% count(member_code) %>% filter(n>1) %>% .$member_code})

membernames %>% filter(member_name %in% {membernames %>% count(member_name) %>% filter(n>1) %>% .$member_name}) %>% select(member_name, member_code) %>% arrange(member_name)
