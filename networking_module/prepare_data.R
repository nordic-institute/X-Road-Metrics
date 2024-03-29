#!/usr/bin/env Rscript

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

starttime <- Sys.time()

duration <- function() { paste('"duration":"', format(as.POSIXct(as.numeric(Sys.time() - starttime, units = 'secs'), origin = as.Date(starttime), tz = "GMT"), format = "%H:%M:%S"), '", ', sep = '') }

library(dplyr)
library(RODBC)
library(jsonlite)

settingsScript <- "/usr/share/xroad-metrics/networking/prepare_data_settings.R"
if (file.exists("./prepare_data_settings.R")){
  settingsScript <- "./prepare_data_settings.R"
}

source(settingsScript)

if (!file.exists(logfile)){
  file.create(logfile)
}

if (!file.exists(heartbeatfile)){
  file.create(heartbeatfile)
}

cat('{"module":"networking_module", ',
    '"local_timestamp":"', as.character(starttime), '", ',
    '"timestamp":', as.numeric(starttime), ', ',
    '"level":"INFO", ',
    '"activity":"starting data preparation", ',
    '"msg":"data preparation script started"}\n',
    file = logfile, append = T, sep = '')

path.data <- paste0('/var/lib/xroad-metrics/networking/dat', profile.suffix,'.rds')
path.dates <- paste0('/var/lib/xroad-metrics/networking/dates', profile.suffix, '.rds')
path.membernames <- paste0('/usr/share/xroad-metrics/networking/membernames', profile.suffix, '.rds')
xroad.descriptor <- settings$networking$"xroad-descriptor-file"
days <- (settings$networking$interval + settings$networking$buffer)
fetchsize <- ifelse(is.null(settings$networking$fetchsize), 100000, settings$networking$fetchsize)

if ("ssl_root_cert" %in% names(settings$postgres) &&
    !is.null(settings$postgres$ssl_root_cert) &&
    !is.na(settings$postgres$ssl_root_cert) &&
    settings$postgres$ssl_root_cert != "") {
  Sys.setenv(PGSSLROOTCERT = settings$postgres$ssl_root_cert)
}

tryCatch(
  con <- odbcDriverConnect(
    connection = paste0(
      "Driver={PostgreSQL UNICODE}",
      ";Server=", settings$postgres$host,
      ";Port=", settings$postgres$port,
      ";Database=opendata_", settings$postgres$suffix,
      ";Uid=", settings$postgres$user,
      ";Pwd=", settings$postgres$password,
      ";UseDeclareFetch=1",
      ";Fetch=", fetchsize,
      ";sslmode=", settings$postgres$ssl_mode,
      ";"
    )
  ),
  error = function(err.msg) {
    cat('{"module":"networking_module", ',
        '"local_timestamp":"', as.character(Sys.time()), '", ',
        '"timestamp":', as.numeric(Sys.time()), ', ',
        duration(),
        '"level":"ERROR", ',
        '"activity":"establish Open data PosgreSQL connection", ',
        '"msg":"', gsub("[\r\n]", "", toString(err.msg)), '"}\n',
        file = logfile, append = T, sep = '')
    cat('{"module":"networking_module", ',
        '"local_timestamp":"', as.character(Sys.time()), '", ',
        '"timestamp":', as.numeric(Sys.time()), ', ',
        '"msg":"FAILED"}',
        file = heartbeatfile, append = F, sep = '')
  }
)

membernames <- NULL

if (file.exists(xroad.descriptor)) {
  tryCatch(
    membernames <- flatten(fromJSON(file(xroad.descriptor))) %>% distinct(member_code, member_name),
    error = function(err.msg) {
      cat('{"module":"networking_module", ',
          '"local_timestamp":"', as.character(Sys.time()), '", ',
          '"timestamp":', as.numeric(Sys.time()), ', ',
          duration(),
          '"level":"ERROR", ',
          '"activity":"read X-Road descriptor file", ',
          '"msg":"', gsub("[\r\n]", "", toString(err.msg)), '"}\n',
          file = logfile, append = T, sep = '')
      cat('{"module":"networking_module", ',
          '"local_timestamp":"', as.character(Sys.time()), '", ',
          '"timestamp":', as.numeric(Sys.time()), ', ',
          '"msg":"FAILED"}',
          file = heartbeatfile, append = F, sep = '')
    }
  )
}

if (!is.null(membernames)) {
  membernames$member_name <- ifelse(
    is.na(membernames$member_name),
    membernames$member_code,
    membernames$member_name
  )
}

tryCatch(
  last.date <- sqlQuery(con, "select requestindate from logs order by requestindate desc limit 1") %>% .[1, 1],
  error = function(err.msg) {
    cat('{"module":"networking_module", ',
        '"local_timestamp":"', as.character(Sys.time()), '", ',
        '"timestamp":', as.numeric(Sys.time()), ', ',
        duration(),
        '"level":"ERROR", ',
        '"activity":"retrieve last date from Open data PosgreSQL database", ',
        '"msg":"', gsub("[\r\n]", "", toString(err.msg)), '"}\n',
        file = logfile, append = T, sep = '')
    cat('{"module":"networking_module", ',
        '"local_timestamp":"', as.character(Sys.time()), '", ',
        '"timestamp":', as.numeric(Sys.time()), ', ',
        '"msg":"FAILED"}',
        file = heartbeatfile, append = F, sep = '')
  }
)

if (!is.null(last.date)) {

  query.string <- paste0(
    "select ",
    "requestindate,clientmembercode,clientsubsystemcode,servicemembercode,servicesubsystemcode,servicecode ",
    "from logs where requestindate >= '",
    last.date, "'::date - interval '", days, " day'",
    " and requestindate <= '",
    last.date, "'::date - interval '", settings$networking$buffer, " day'",
    " and succeeded=TRUE")

  tryCatch(
    odbcQuery(con, query.string),
    error = function(err.msg) {
      cat('{"module":"networking_module", ',
          '"local_timestamp":"', as.character(Sys.time()), '", ',
          '"timestamp":', as.numeric(Sys.time()), ', ',
          duration(),
          '"level":"ERROR", ',
          '"activity":"retrieve logs from Open data PosgreSQL database", ',
          '"msg":"', gsub("[\r\n]", "", toString(err.msg)), '"}\n',
          file = logfile, append = T, sep = '')
      cat('{"module":"networking_module", ',
          '"local_timestamp":"', as.character(Sys.time()), '", ',
          '"timestamp":', as.numeric(Sys.time()), ', ',
          '"msg":"FAILED"}',
          file = heartbeatfile, append = F, sep = '')
    }
  )

  dates <- c(NA, NA, settings$xroad$instance)
  dat2 <- data.frame()

  dat <- odbcFetchRows(con, max=fetchsize)$data %>% as.data.frame(stringsAsFactors=FALSE)
  while (nrow(dat) > 0) {
    colnames(dat) <- c(
      "requestindate", "clientmembercode", "clientsubsystemcode",
      "servicemembercode", "servicesubsystemcode", "servicecode"
    )
    dat[is.na(dat)] <- ''
    min_date <- min(dat$requestindate)
    max_date <- max(dat$requestindate)
    dates[1] <- min(dates[1], min_date, na.rm = TRUE)
    dates[2] <- max(dates[2], max_date, na.rm = TRUE)

    dat <- dat %>%
      count(clientmembercode, clientsubsystemcode, servicemembercode, servicesubsystemcode, servicecode)

    dat2 <- rbind(dat2, dat)
    dat2 <- dat2 %>%
      group_by(clientmembercode, clientsubsystemcode, servicemembercode, servicesubsystemcode, servicecode) %>%
      summarize_at(vars(n), sum) %>%
      as.data.frame(stringsAsFactors=FALSE)

    dat <- odbcFetchRows(con, max=fetchsize)$data %>% as.data.frame(stringsAsFactors=FALSE)
  }
  odbcClose(con)

  if (nrow(dat2) > 0) {
    saveRDS(dates, path.dates)

    dat2 <- dat2 %>%
      mutate(
        client = paste(clientmembercode, clientsubsystemcode, sep = '\n'),
        producer = paste(servicemembercode, servicesubsystemcode, sep = '\n'),
        producer.service = paste(servicemembercode, servicesubsystemcode, servicecode, sep = '\n')
      ) %>%
      as.data.frame

    dat2$metaservice <- as.integer(ifelse(dat2$servicecode %in% settings$networking$metaservices, 1, 0))

    if (!is.null(membernames)) {
      dat2 <- left_join(dat2, membernames, by = c('clientmembercode' = 'member_code')) %>%
        rename(clientmembername = member_name) %>%
        left_join(., membernames, by = c('servicemembercode' = 'member_code')) %>%
        rename(servicemembername = member_name)
    } else {
      dat2$clientmembername <- dat2$clientmembercode
      dat2$servicemembername <- dat2$servicemembercode
    }

    dat2 <- dat2 %>%
      mutate(
        client.name = paste(clientmembername, clientsubsystemcode, sep = '\n'),
        producer.name = paste(servicemembername, servicesubsystemcode, sep = '\n'),
        producer.service.name = paste(servicemembername, servicesubsystemcode, servicecode, sep = '\n')
      )

    dat2[is.na(dat2)] <- ' '

    tryCatch({
      saveRDS(dat2, path.data)
    }, error = function(err.msg) {
      cat('{"module":"networking_module", ',
          '"local_timestamp":"', as.character(Sys.time()), '", ',
          '"timestamp":', as.numeric(Sys.time()), ', ',
          duration(),
          '"level":"ERROR", ',
          '"activity":"prepare data and save for visualizer", ',
          '"msg":"', gsub("[\r\n]", "", toString(err.msg)), '"}\n',
          file = logfile, append = T, sep = '')
      cat('{"module":"networking_module", ',
          '"local_timestamp":"', as.character(Sys.time()), '", ',
          '"timestamp":', as.numeric(Sys.time()), ', ',
          '"msg":"FAILED"}',
          file = heartbeatfile, append = F, sep = '')
    })
  } else {
    cat('{"module":"networking_module", ',
        '"local_timestamp":"', as.character(Sys.time()), '", ',
        '"timestamp":', as.numeric(Sys.time()), ', ',
        duration(),
        '"level":"ERROR", ',
        '"activity":"retrieve logs from Open data PosgreSQL database", ',
        '"msg":"no data in the Open data PostgreSQL database for the specified time frame"}\n',
        file = logfile, append = T, sep = '')
    cat('{"module":"networking_module", ',
        '"local_timestamp":"', as.character(Sys.time()), '", ',
        '"timestamp":', as.numeric(Sys.time()), ', ',
        '"msg":"FAILED"}',
        file = heartbeatfile, append = F, sep = '')

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
      file = logfile, append = T, sep = '')
  cat('{"module":"networking_module", ',
      '"local_timestamp":"', as.character(Sys.time()), '", ',
      '"timestamp":', as.numeric(Sys.time()), ', ',
      '"msg":"SUCCEEDED"}',
      file = heartbeatfile, append = F, sep = '')
}
