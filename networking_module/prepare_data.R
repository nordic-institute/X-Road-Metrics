starttime<-Sys.time()

duration<-function() {paste('"duration":"', format(as.POSIXct(as.numeric(Sys.time()-starttime, units='secs'), origin = as.Date(starttime), tz = "GMT"), format = "%H:%M:%S"), '", ', sep='')}

args<-commandArgs(trailingOnly = F)  
scriptPath<-normalizePath(dirname(sub("^--file=", "", args[grep("^--file=", args)])))

setwd(scriptPath)

cat('{"module":"networking_module", ', 
      '"local_timestamp":"', as.character(starttime), '", ',
      '"timestamp":', as.numeric(starttime), ', ',
      '"level":"INFO", ', 
      '"activity":"starting data preparation", ',
      '"msg":"data preparation script started"}\n',
      file='logs/prepare_data_log.json', append=T, sep='')

library(dplyr)
library(RPostgreSQL)
library(jsonlite)
      
source('prepare_data_settings.R')

path.data<-paste0('/srv/shiny-server/', instancename, '/dat.rds')
path.dates<-paste0('/srv/shiny-server/', instancename, '/dates.rds')
path.membernames<-paste0('/srv/app/', instancename, '/membernames.rds')
riha<-paste0('riha_', instancename, '.json')
days<-interval+buffer

tryCatch({
  con <- dbConnect(dbDriver("PostgreSQL"), dbname = dbname,
                   host = host, port = port,
                   user = user, password = pwd)
}, error = function(err.msg){
  cat('{"module":"networking_module", ', 
      '"local_timestamp":"', as.character(Sys.time()), '", ',
      '"timestamp":', as.numeric(Sys.time()), ', ',
      duration(),
      '"level":"ERROR", ', 
      '"activity":"establish Open data PosgreSQL connection", ',
      '"msg":"', gsub("[\r\n]", "", toString(err.msg)), '"}\n',
      file='logs/prepare_data_log.json', append=T, sep='')
  cat('{"module":"networking_module", ', 
      '"local_timestamp":"', as.character(Sys.time()), '", ',
      '"timestamp":', as.numeric(Sys.time()), ', ',
      '"msg":"FAILED"}', 
      file='heartbeat/prepare_data_heartbeat.json', append=F, sep='')
}
)

#dbExistsTable(con, 'logs')

tryCatch({
membernames<-flatten(fromJSON(file(riha))) %>% distinct(member_code, member_name)
}, error = function(err.msg){
  cat('{"module":"networking_module", ', 
      '"local_timestamp":"', as.character(Sys.time()), '", ',
      '"timestamp":', as.numeric(Sys.time()), ', ',
      duration(),
      '"level":"ERROR", ', 
      '"activity":"read riha.json", ',
      '"msg":"', gsub("[\r\n]", "", toString(err.msg)), '"}\n',
      file='logs/prepare_data_log.json', append=T, sep='')
  cat('{"module":"networking_module", ', 
      '"local_timestamp":"', as.character(Sys.time()), '", ',
      '"timestamp":', as.numeric(Sys.time()), ', ',
      '"msg":"FAILED"}', 
      file='heartbeat/prepare_data_heartbeat.json', append=F, sep='')
}
)

membernames$member_name<-ifelse(is.na(membernames$member_name), membernames$member_code, membernames$member_name)

tryCatch({
last.date<-dbGetQuery(con, "select requestindate from logs order by requestindate desc limit 1") %>% .[1,1]
}, error = function(err.msg){
  cat('{"module":"networking_module", ', 
      '"local_timestamp":"', as.character(Sys.time()), '", ',
      '"timestamp":', as.numeric(Sys.time()), ', ',
      duration(),
      '"level":"ERROR", ', 
      '"activity":"retrieve last date from Open data PosgreSQL database", ',
      '"msg":"', gsub("[\r\n]", "", toString(err.msg)), '"}\n',
      file='logs/prepare_data_log.json', append=T, sep='')
  cat('{"module":"networking_module", ', 
      '"local_timestamp":"', as.character(Sys.time()), '", ',
      '"timestamp":', as.numeric(Sys.time()), ', ',
      '"msg":"FAILED"}', 
      file='heartbeat/prepare_data_heartbeat.json', append=F, sep='')
}
)

if (!is.null(last.date)) {

query.string<-paste0("select requestindate,clientmembercode,clientsubsystemcode,servicemembercode,servicesubsystemcode,servicecode from logs where requestindate >= '", 
                       last.date, "'::date - interval '", days, " day'",
                       " and requestindate <= '",
                       last.date, "'::date - interval '", buffer, " day'",
                       " and succeeded=TRUE")

tryCatch({                    
  dat<-dbGetQuery(con, query.string)
}, error = function(err.msg){
  cat('{"module":"networking_module", ', 
      '"local_timestamp":"', as.character(Sys.time()), '", ',
      '"timestamp":', as.numeric(Sys.time()), ', ',
      duration(),
      '"level":"ERROR", ', 
      '"activity":"retrieve logs from Open data PosgreSQL database", ',
      '"msg":"', gsub("[\r\n]", "", toString(err.msg)), '"}\n',
      file='logs/prepare_data_log.json', append=T, sep='')
  cat('{"module":"networking_module", ', 
      '"local_timestamp":"', as.character(Sys.time()), '", ',
      '"timestamp":', as.numeric(Sys.time()), ', ',
      '"msg":"FAILED"}', 
      file='heartbeat/prepare_data_heartbeat.json', append=F, sep='')
}
)

if (nrow(dat)>0) {

dates<-c(as.character(min(dat$requestindate)), as.character(max(dat$requestindate)), instancename)
saveRDS(dates, path.dates)

dat[is.na(dat)]<-''

dat2<-dat %>% count(clientmembercode, clientsubsystemcode, servicemembercode, servicesubsystemcode, servicecode) %>% 
  mutate(
    client=paste(clientmembercode, clientsubsystemcode, sep='\n'), 
    producer=paste(servicemembercode, servicesubsystemcode, sep='\n'), 
    producer.service=paste(servicemembercode, servicesubsystemcode, servicecode, sep='\n')
  ) %>% 
  as.data.frame

dat2$metaservice<-as.integer(ifelse(dat2$servicecode %in% metaservices, 1, 0))

dat2<-left_join(dat2, membernames, by=c('clientmembercode'='member_code')) %>% 
  rename(clientmembername=member_name) %>% 
  left_join(., membernames, by=c('servicemembercode'='member_code')) %>% 
  rename(servicemembername=member_name)
  
dat2<-dat2 %>% 
  mutate(
    client.name=paste(clientmembername, clientsubsystemcode, sep='\n'), 
    producer.name=paste(servicemembername, servicesubsystemcode, sep='\n'), 
    producer.service.name=paste(servicemembername, servicesubsystemcode, servicecode, sep='\n')
  )

dat2[is.na(dat2)]<-' '

tryCatch({
saveRDS(dat2, path.data)
}, error = function(err.msg){
  cat('{"module":"networking_module", ', 
      '"local_timestamp":"', as.character(Sys.time()), '", ',
      '"timestamp":', as.numeric(Sys.time()), ', ',
      duration(),
      '"level":"ERROR", ', 
      '"activity":"prepare data and save for visualizer", ',
      '"msg":"', gsub("[\r\n]", "", toString(err.msg)), '"}\n',
      file='logs/prepare_data_log.json', append=T, sep='')
  cat('{"module":"networking_module", ', 
      '"local_timestamp":"', as.character(Sys.time()), '", ',
      '"timestamp":', as.numeric(Sys.time()), ', ',
      '"msg":"FAILED"}', 
      file='heartbeat/prepare_data_heartbeat.json', append=F, sep='')
})
} else {
  cat('{"module":"networking_module", ', 
      '"local_timestamp":"', as.character(Sys.time()), '", ',
      '"timestamp":', as.numeric(Sys.time()), ', ',
      duration(),
      '"level":"ERROR", ', 
      '"activity":"retrieve logs from Open data PosgreSQL database", ',
      '"msg":"no data in the Open data PostgreSQL database for the specified time frame"}\n',
      file='logs/prepare_data_log.json', append=T, sep='')
  cat('{"module":"networking_module", ', 
      '"local_timestamp":"', as.character(Sys.time()), '", ',
      '"timestamp":', as.numeric(Sys.time()), ', ',
      '"msg":"FAILED"}', 
      file='heartbeat/prepare_data_heartbeat.json', append=F, sep='')
  
  }
}

if (exists("dat2")) {
  cat('{"module":"networking_module", ', 
      '"local_timestamp":"', as.character(Sys.time()), '", ',
      '"timestamp":', as.numeric(Sys.time()), ', ',
      duration(),
      '"level":"INFO", ', 
      '"activity":"data preparation ended", ',
      '"msg":"', nrow(dat2), ' rows were written for visualizer"}\n',
      file='logs/prepare_data_log.json', append=T, sep='')
  cat('{"module":"networking_module", ', 
      '"local_timestamp":"', as.character(Sys.time()), '", ',
      '"timestamp":', as.numeric(Sys.time()), ', ',
      '"msg":"SUCCEEDED"}', 
      file='heartbeat/prepare_data_heartbeat.json', append=F, sep='')
}

