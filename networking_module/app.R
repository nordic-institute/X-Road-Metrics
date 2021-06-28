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

library(shiny)
library(dplyr)
library(shinycssloaders)
library(qgraph)
library(ggplot2)

rdsPath <- "/var/lib/xroad-metrics/networking"

####ui####
ui <- fluidPage(
  title = "X-Road Members Networking Visualization",
  tags$script(HTML('Shiny.addCustomMessageHandler("changetitle", function(title) {document.title=title});')),

  fluidRow(
    tags$div(
      tags$img(src = "xroad-metrics-100.png", align = "left"),
      tags$img(src = "eu_rdf_100_en.png", align = "right")
    ),
    style = "margin: 0"
  ),

  fluidRow(
    tags$div(
      tags$h3(textOutput('heading'), align = 'center', style = "color:#663cdc")
    )
  ),

  wellPanel(htmlOutput('text1') %>% withSpinner(color = '#663cdc'), style = "padding: 5px;"),

  inputPanel(
    selectizeInput('memberSelection1', label = 'Select member:', choices = NULL),
    sliderInput('thresh1', label = 'Select threshold (top n number of queries)', min = 1, max = 500, value = 25),
    radioButtons('detail1', 'Select the level of details', choices = c('Member level' = 'member', 'Subsystem level' = 'subsystem', 'Service level' = 'service'), selected = 'member'),
    radioButtons('membername1', 'Display members as', choices = c('Name' = 'name', 'Registry code' = 'code'), selected = 'name'),
    radioButtons('metaservices1', 'Include metaservices', choices = c('No' = 0, 'Yes' = 1), selected = 0)
  ),

  plotOutput('net1', height = "800px") %>% withSpinner(color = '#663cdc'),
  br(),
  plotOutput('ggplot1', height = "800px") %>% withSpinner(color = '#663cdc'),
  wellPanel(
    div("The X-Road Metrics tools are developed by  ", tags$a(href = "https://www.niis.org", "NIIS.", target = "_blank"), style = "padding: 5px;"),
    div("X-Road Metrics  ", tags$a(href = "https://x-road.global/xroad-metrics-licence-info", "licence info.", target = "_blank"), style = "padding: 5px;")
  )
)

####server####
server <- function(input, output, session) {

  reactives <- reactiveValues()

  #React to changes in URL query parameters
  observeEvent(session$clientData$url_search,
  {
    query <- parseQueryString(session$clientData$url_search)
    profile.suffix <- if ("profile" %in% names(query)) paste0("_", query[["profile"]]) else ""
    reactives$dat <- readRDS(paste0(rdsPath, "/dat", profile.suffix, ".rds"))
    reactives$dates <- readRDS(paste0(rdsPath, "/dates", profile.suffix, ".rds"))
    reactives$xroadInstance <- reactives$dates[3]

    session$sendCustomMessage(
      "changetitle",
      paste0("X-Road ", reactives$xroadInstance, " Members Networking Visualization"))

    updateSelectizeInput(
      session,
      'memberSelection1',
      choices = c(
        'All members',
        sort(union(
          unique(reactives$dat$servicemembername),
          unique(reactives$dat$clientmembername)
        ))
      ),
      selected = 'All members',
      server = TRUE
    )
  })

  output$heading <- renderText({
    paste0('X-Road Metrics: X-Road Networking Visualization for instance ', reactives$xroadInstance)
  })

  output$text1 <- renderText({
    paste0(
      'X-Road Metrics: X-Road Networking Visualization for instance ',
      reactives$xroadInstance,
      ', from ', reactives$dates[1], ' to ', reactives$dates[2], '.')
  })

  member <- reactive({
    if (is.null(member)) { return(0) }
    else
      input$memberSelection1
  })

  dat2 <- reactive({
    if (input$metaservices1 == 0) {
      reactives$dat %>% filter(metaservice == 0)
    } else {
      reactives$dat
    }
  })

  net <- reactive({

    if (input$memberSelection1 == 'All members') {

      switch(input$detail1,
             member = dat2() %>%
               group_by(clientmembercode, servicemembercode, clientmembername, servicemembername) %>%
               summarize_at(vars(n), funs(nn = sum)) %>%
               ungroup %>%
               mutate(nn = log10(nn + 1)) %>%
               top_n(input$thresh1, nn),
             subsystem = dat2() %>%
               group_by(client, producer, client.name, producer.name) %>%
               summarize_at(vars(n), funs(nn = sum)) %>%
               ungroup %>%
               mutate(nn = log10(nn + 1)) %>%
               top_n(input$thresh1, nn),
             service = dat2() %>%
               group_by(client, producer.service, client.name, producer.service.name) %>%
               summarize_at(vars(n), funs(nn = sum)) %>%
               ungroup %>%
               mutate(nn = log10(nn + 1)) %>%
               top_n(input$thresh1, nn)
      )

    } else {

      switch(input$detail1,
             member = dat2() %>%
               filter(clientmembername == input$memberSelection1 |
                        servicemembername == input$memberSelection1) %>%
               group_by(clientmembercode, servicemembercode, clientmembername, servicemembername) %>%
               summarize_at(vars(n), funs(nn = sum)) %>%
               ungroup %>%
               mutate(nn = log10(nn + 1)) %>%
               top_n(input$thresh1, nn),
             subsystem = dat2() %>%
               filter(clientmembername == input$memberSelection1 |
                        servicemembername == input$memberSelection1) %>%
               group_by(client, producer, client.name, producer.name) %>%
               summarize_at(vars(n), funs(nn = sum)) %>%
               ungroup %>%
               mutate(nn = log10(nn + 1)) %>%
               top_n(input$thresh1, nn),
             service = dat2() %>%
               filter(clientmembername == input$memberSelection1 |
                        servicemembername == input$memberSelection1) %>%
               group_by(client, producer.service, client.name, producer.service.name) %>%
               summarize_at(vars(n), funs(nn = sum)) %>%
               ungroup %>%
               mutate(nn = log10(nn + 1)) %>%
               top_n(input$thresh1, nn)
      )
    }
  })

  output$net1 <- renderPlot({
    validate(need(nrow(net()) > 0, "No data"))
    if (input$membername1 == 'code') {
      qgraph(net()[, c(1, 2, 5)], edgelist = T, label.scale = F, borders = T, border.color = '#00c8e6', edge.color = '#663cdc')
    } else {
      qgraph(net()[, c(3:5)], edgelist = T, label.scale = F, borders = T, border.color = '#00c8e6', edge.color = '#663cdc')
    }
  })

  output$ggplot1 <- renderPlot({

    validate(need(nrow(net()) > 0, "No data"))

    if (input$membername1 == 'code') {

      ggplot(
      {
        if (nrow(net()) == 1) {
          cbind(
            t(sapply(net()[, 1:2], function(x) gsub('\n', '/', x))),
            data.frame(nn = net()[, 5])
          )
        } else {
          cbind(
            sapply(net()[, 1:2], function(x) gsub('\n', '/', x)),
            data.frame(nn = net()[, 5])
          ) }
      },
        aes_string(names(net())[2], names(net())[1], fill = 'nn')) +
        theme_minimal(base_size = 18) +
        theme(axis.text.x = element_text(angle = 90, hjust = 1, vjust = 0.5)) +
        coord_fixed(ratio = 1) +
        geom_tile() +
        scale_fill_gradientn(values = c(1, 0.9, 0.5, 0),
                             colours = c("firebrick", "red", "yellow", "green"),
                             name = "Number of queries\n(logarithmed)\n")
    } else {

      ggplot(
      {
        if (nrow(net()) == 1) {
          cbind(
            t(sapply(net()[, 3:4], function(x) gsub('\n', '/', x))),
            data.frame(nn = net()[, 5])
          )
        } else {
          cbind(
            sapply(net()[, 3:4], function(x) gsub('\n', '/', x)),
            data.frame(nn = net()[, 5])
          ) }
      },
        aes_string(names(net())[4], names(net())[3], fill = 'nn')) +
        theme_minimal(base_size = 18) +
        theme(axis.text.x = element_text(angle = 90, hjust = 1, vjust = 0.5)) +
        coord_fixed(ratio = 1) +
        geom_tile() +
        scale_fill_gradientn(values = c(1, 0.9, 0.5, 0),
                             colours = c("firebrick", "red", "yellow", "green"),
                             name = "Number of queries\n(logarithmed)\n")

    }
  })


}

shinyApp(ui = ui, server = server)
