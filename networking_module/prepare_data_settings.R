library("yaml")

args <- commandArgs(trailingOnly = TRUE)
profile.suffix <- ""

if (length(args) >= 2 && args[1] == "--profile") {
  profile.suffix <- paste0("_", args[2])
}

settings_file_name <- paste0("settings", profile.suffix, ".yaml")

settings <- tryCatch(
  yaml.load_file(paste0("./", settings_file_name)),
  error=function(cond) {
    message(cond)
    return(
      yaml.load_file(paste0("/etc/xroad-metrics/networking/", settings_file_name))
    )
  }
)

#postgres doesn't like uppercase or dashes
settings$postgres$suffix <- tolower(gsub("-", "_",settings$xroad$instance))

logfile <- paste0(settings$logger$"log-path", "/prepare_data_log.json")
heartbeatfile <- paste0(settings$logger$"heartbeat-path", "/prepare_data_heartbeat.json")
