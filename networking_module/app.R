library(shiny)
library(dplyr)
library(shinycssloaders)
library(qgraph)
library(ggplot2)

dat<-readRDS("dat.rds")
dates<-readRDS("dates.rds")

allMemberNames<-c('All members', sort(union(unique(dat$servicemembername), unique(dat$clientmembername))))

####ui####
ui <- fluidPage(title=paste0("X-road members networking visualization, instance ", dates[3]),

  fluidRow(
    tags$div(
      tags$img(src = "ria_100_en.png", align = "left"),
      tags$img(src = "xroad_100_en.png", align = "left"),
      tags$img(src = "eu_rdf_100_en.png", align = "right")
    )
  ),
  
  fluidRow(
    tags$div(
      tags$h3(paste0('X-Road v6 usage statistics: members networking visualization, instance ', dates[3]), align='center', style="color:#663cdc")
    )
  ),

  wellPanel(htmlOutput('text1') %>% withSpinner(color='#663cdc'), style = "padding: 5px;"),
  
  inputPanel(
  
  selectizeInput('memberSelection1', label='Select member:', choices=allMemberNames, selected='All members'),
  
  sliderInput('thresh1', label = 'Select threshold (top n number of queries)', min = 1, max = 500, value = 25),

  radioButtons('detail1', 'Select the level of details', choices=c('Member level'='member', 'Subsystem level'='subsystem', 'Service level'='service'), selected='member'),
  
  radioButtons('membername1', 'Display members as', choices=c('Name'='name', 'Registry code'='code'), selected='name'),
  
  radioButtons('metaservices1', 'Include metaservices', choices=c('No'=0, 'Yes'=1), selected=0)
  
  ),

  plotOutput('net1', height = "800px") %>% withSpinner(color='#663cdc'),
  
  br(),
  
  plotOutput('ggplot1', height = "800px") %>% withSpinner(color='#663cdc'),
  
  wellPanel("The visualization application was developed by ", tags$a(href = "https://www.stacc.ee", "Tarkvara Tehnoloogia Arenduskeskus OÜ (STACC)", target="_blank"), style = "padding: 5px;")
  

)

####server####
server <- function(input, output, session){
  
  output$text1<-renderText({
    paste0('The visualization is based on the X-road monitoring data, instance ', tags$a(href=paste0('https://logs.x-tee.ee/', dates[3],'/gui/'), dates[3], target="_blank"),', from ', dates[1], ' to ', dates[2], '.')
  })
  
  member<-reactive({
    if (is.null(member)) {return(0)}
    else
      input$memberSelection1
  })
  
  dat2<-reactive({
    if (input$metaservices1==0) {
      dat %>% filter(metaservice==0)
    } else {
      dat
    }
  })
  
  net<-reactive({

    if (input$memberSelection1=='All members') {
      
      switch(input$detail1,
             member=dat2() %>%
               group_by(clientmembercode, servicemembercode, clientmembername, servicemembername) %>%
               summarize_at(vars(n), funs(nn=sum)) %>% ungroup %>% 
               mutate(nn=log10(nn+1)) %>% top_n(input$thresh1, nn),
             subsystem=dat2() %>% 
               group_by(client, producer, client.name, producer.name) %>%
               summarize_at(vars(n), funs(nn=sum)) %>% ungroup %>% 
               mutate(nn=log10(nn+1)) %>% top_n(input$thresh1, nn),
             service=dat2() %>% 
               group_by(client, producer.service, client.name, producer.service.name) %>%
               summarize_at(vars(n), funs(nn=sum)) %>% ungroup %>% 
               mutate(nn=log10(nn+1)) %>% top_n(input$thresh1, nn)
      )
      
    } else {
      
      switch(input$detail1,
             member=dat2() %>% filter(clientmembername==input$memberSelection1 | 
                                      servicemembername==input$memberSelection1) %>% 
               group_by(clientmembercode, servicemembercode, clientmembername, servicemembername) %>%
               summarize_at(vars(n), funs(nn=sum)) %>% ungroup %>% 
               mutate(nn=log10(nn+1)) %>% top_n(input$thresh1, nn),
             subsystem=dat2() %>% filter(clientmembername==input$memberSelection1 | 
                                         servicemembername==input$memberSelection1) %>% 
               group_by(client, producer, client.name, producer.name) %>%
               summarize_at(vars(n), funs(nn=sum)) %>% ungroup %>% 
               mutate(nn=log10(nn+1)) %>% top_n(input$thresh1, nn),
             service=dat2() %>% filter(clientmembername==input$memberSelection1 | 
                                       servicemembername==input$memberSelection1) %>% 
               group_by(client, producer.service, client.name, producer.service.name) %>%
               summarize_at(vars(n), funs(nn=sum)) %>% ungroup %>% 
               mutate(nn=log10(nn+1)) %>% top_n(input$thresh1, nn)
      )
    }
  })
 
  output$net1<-renderPlot({
    validate(need(nrow(net()) > 0, "No data"))
    if (input$membername1=='code'){
      qgraph(net()[,c(1,2,5)], edgelist=T, label.scale=F, borders=T, border.color='#00c8e6', edge.color='#663cdc')
    } else {
      qgraph(net()[,c(3:5)], edgelist=T, label.scale=F, borders=T, border.color='#00c8e6', edge.color='#663cdc')
    }
  })
  
  output$ggplot1<-renderPlot({
    
    validate(need(nrow(net()) > 0, "No data"))
    
    if (input$membername1=='code'){
      
    ggplot(
      {
      if (nrow(net())==1) {
        cbind(
          t(sapply(net()[,1:2], function(x) gsub('\n', '/', x))),
          data.frame(nn=net()[,5])
        )
      } else {
        cbind(
          sapply(net()[,1:2], function(x) gsub('\n', '/', x)),
          data.frame(nn=net()[,5])
        )}
      }, 
      aes_string(names(net())[2], names(net())[1], fill='nn')) +
      theme_minimal(base_size=18) +
      theme(axis.text.x=element_text(angle=90, hjust=1, vjust=0.5)) +
      coord_fixed(ratio=1) + geom_tile() +
      scale_fill_gradientn(values=c(1, 0.9, 0.5, 0), 
                           colours=c("firebrick", "red", "yellow", "green"),
                           name="Number of queries\n(logarithmed)\n")
    } else {
      
      ggplot(
        {
          if (nrow(net())==1) {
            cbind(
              t(sapply(net()[,3:4], function(x) gsub('\n', '/', x))),
              data.frame(nn=net()[,5])
            )
          } else {
            cbind(
              sapply(net()[,3:4], function(x) gsub('\n', '/', x)),
              data.frame(nn=net()[,5])
            )}
        }, 
        aes_string(names(net())[4], names(net())[3], fill='nn')) +
        theme_minimal(base_size=18) +
        theme(axis.text.x=element_text(angle=90, hjust=1, vjust=0.5)) +
        coord_fixed(ratio=1) + geom_tile() +
        scale_fill_gradientn(values=c(1, 0.9, 0.5, 0), 
                             colours=c("firebrick", "red", "yellow", "green"),
                             name="Number of queries\n(logarithmed)\n")
      
    }
  })
  

}

shinyApp(ui = ui, server = server)
