var incident_table = initialize_incident_table('#incident_table', 'get_incident_data_serverside', '#toggle-service-call-incident', "#incident-add-constraint-column", "#incident-alert")

$("#new-selector").click(function () {
    $('#incident_table').DataTable().draw();
    
    $("#incident-alert").removeClass('alert-success')
    $("#incident-alert").html("")
});

$("#history-selector").click(function () {
    
    $("#history-alert").removeClass('alert-success')
    $("#history-alert").html("")
    
    var clicks = $("#history-selector").data('clicks');
    if (clicks) {
        $('#history_table').DataTable().draw();
    } else {
       var history_table = initialize_incident_table('#history_table', 'get_historic_incident_data_serverside', '#toggle-service-call-history', "#history-add-constraint-column", "#history-alert")
    }
    $("#history-selector").data("clicks", true);
});

function initialize_incident_table(table_id, serverside_url, service_call_toggle_id, new_constraint_column_id, alert_id) {
    $.ajax({
        url: "get_incident_table_initialization_data",
        method: 'GET',
        data: {table_id: JSON.stringify(table_id)},
        dataType: 'json',
        success: function(response){
            
            $(table_id).html(response.html)
            
            var table = $(table_id).DataTable( {
                scrollX: true,
                order: response.order,
                serverSide: true,
                processing: true,
                retrieve: true,
                searching: false,
                cache: false,
                ajax: {
                    url: serverside_url,
                    type: "POST",
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    data: function ( d ) {
                        d.filterConstraints = JSON.stringify(getConstraints($(new_constraint_column_id).parent().parent().find('.constraints')))
                    },
                    error: function (xhr, error, thrown) {
                        $(alert_id).html(xhr.responseText);
                        $(alert_id).addClass('alert-danger')
                    }
                },
                columns: response.columns,
                columnDefs: [ { targets: response.service_call_field_idxs, visible: false},
                    {
                    "targets": response.comment_field_idx,
                    "className": "comment-cell",
                    },
                     {
                    "targets": -2,
                    "data": null,
                    "defaultContent": '<button type="button" class="btn btn-default btn-examples" data-toggle="modal" data-target="#example-requests-modal">See examples</button><button type="button" class="btn btn-default btn-filter-similar">Filter similar</button>'
                    },
                    {
                    "targets": -1,
                    "data": null,
                    "render": function(data, type, full, meta){
                        
                       if(response.historic_averages_anomaly_types.indexOf(full[response.anomaly_type_idx]) >= 0) {
                           data = '<button type="button" class="btn btn-default btn-status btn-incident">Incident</button><button type="button" class="btn btn-default btn-status btn-viewed">Viewed</button><button type="button" class="btn btn-default btn-status btn-normal">Normal</button>';
                       }
                       else {
                          data = '<button type="button" class="btn btn-default btn-status btn-viewed">Viewed</button>';
                       }
                       return data;
                    }
                } ]
            } );
            
            $(service_call_toggle_id).on( 'click', function (e) {
                e.preventDefault();

                for (i = 0; i < response.service_call_field_idxs.length + 1; i++) { 
                    var column = table.column( i );
                    column.visible( ! column.visible() );
                }
            } );
            
            $(new_constraint_column_id).html(response.filter_selector_html)
            $(new_constraint_column_id).trigger('change')
            
            return table;
        }
    });
}

$(document).on('click', '.comment-cell', function(){
   $('#comments-modal').modal('toggle');
    var cell = $(this)
    $(this).addClass("comment-updated")
    $("#comments-textarea").val($(this).html())
    $('#comments-modal').off('hidden.bs.modal');
    $('#comments-modal').on('hidden.bs.modal', function () {
       cell.html($("#comments-textarea").val())
    });
});



$(document).on('click', '.btn-status', function(){

    $(this).closest("td").find('.btn-status').css('border-color','#ccc');
    $(this).closest("td").find('.btn-status').css('border-width','1px');

    if (!$(this).hasClass( "selected" )) {
        $(this).css('border-width','3px');

        if ($(this).hasClass( "btn-incident" )) {
            $(this).css('border-color','red');
        } else if ($(this).hasClass( "btn-normal" )) {
            $(this).css('border-color','green');
        } else {
            $(this).css('border-color','yellow');
        }
        $(this).closest("td").find('.btn-status').removeClass( "selected" );
        $(this).addClass( "selected" )
    } else {
        $(this).closest("td").find('.btn-status').removeClass( "selected" );
    }
});



$(document).on('click', '.btn-examples', function(){
    var incident_id = $(this).closest('tr').attr('id');
    
    $.ajax({
        url: "get_request_list",
        method: 'GET',
        data: {incident_id: JSON.stringify(incident_id)},
        dataType: 'json',
        success: function(response){
            $('#example_request_table').DataTable( {
                data: response.requests,
                columns: response.columns,
                destroy: true,
                searching: false
            } );
        }
    });

});

$(document).on('click', '.btn-filter-similar', function(){
    
    var table = $(this).closest('table').DataTable()
    var data = table.row( $(this).parents('tr') ).data();
    var columns = table.settings().init().columns;
    
    for (i = 1; i < columns.length-2; i++) { 
        var column = columns[i].name;
        var operator = "="
        var value = data[i];
        var data_type = columns[i].data_type
        
        $('<button>', {
            text: column + ' ' + operator + ' ' + value,
            class: 'constraint btn btn-info'
        }).appendTo($(this).parents().find('.constraints')).data('column', column).data('operator', operator).data('value', value).data('data-type', data_type);
    }
    
});

$('.btn-mark-all-incidents').click(function(){
    
    if ($("ul#new-vs-history-selector li.active").attr('id') === "new-selector") {
        table_id = '#incident_table'
    } else {
        table_id = '#history_table'
    }
    
    $(table_id).find('.btn-status').css('border-color','#ccc');
    $(table_id).find('.btn-status').css('border-width','1px');
    $(table_id).find('.btn-status').removeClass( "selected" );

    $(table_id).find('.btn-incident').css('border-color','red');
    $(table_id).find('.btn-incident').css('border-width','3px');
    $(table_id).find('.btn-incident').addClass( "selected" )

});

$('.btn-mark-all-viewed').click(function(){
    
    if ($("ul#new-vs-history-selector li.active").attr('id') === "new-selector") {
        table_id = '#incident_table'
    } else {
        table_id = '#history_table'
    }
    
    $(table_id).find('.btn-status').css('border-color','#ccc');
    $(table_id).find('.btn-status').css('border-width','1px');
    $(table_id).find('.btn-status').removeClass( "selected" );
    
    $(table_id).find('.btn-viewed').css('border-color','yellow');
    $(table_id).find('.btn-viewed').css('border-width','3px');
    $(table_id).find('.btn-viewed').addClass( "selected" )

});

$('.btn-mark-all-normal').click(function(){
    
    if ($("ul#new-vs-history-selector li.active").attr('id') === "new-selector") {
        table_id = '#incident_table'
    } else {
        table_id = '#history_table'
    }
    
    $(table_id).find('.btn-status').css('border-color','#ccc');
    $(table_id).find('.btn-status').css('border-width','1px');
    $(table_id).find('.btn-status').removeClass( "selected" );
    
    $(table_id).find('.btn-normal').css('border-color','green');
    $(table_id).find('.btn-normal').css('border-width','3px');
    $(table_id).find('.btn-normal').addClass( "selected" )

});

$('.btn-unmark-all').click(function(){
    
    if ($("ul#new-vs-history-selector li.active").attr('id') === "new-selector") {
        table_id = '#incident_table'
    } else {
        table_id = '#history_table'
    }
    
    $(table_id).find('.btn-status').css('border-color','#ccc');
    $(table_id).find('.btn-status').css('border-width','1px');
    $(table_id).find('.btn-status').removeClass( "selected" );

});

$('.btn-save').click(function(){
    
    if ($("ul#new-vs-history-selector li.active").attr('id') === "new-selector") {
        table_id = '#incident_table'
        alert_id = '#incident-alert'
    } else {
        table_id = '#history_table'
        alert_id = '#history-alert'
    }
    
    var normal_ids = []
    $(table_id).find('.btn-normal.selected').each(function () {
      normal_ids.push($(this).closest('tr').attr('id'));
    });
    
    var incident_ids = []
    $(table_id).find('.btn-incident.selected').each(function () {
      incident_ids.push($(this).closest('tr').attr('id'));
    });
    
    var viewed_ids = []
    $(table_id).find('.btn-viewed.selected').each(function () {
      viewed_ids.push($(this).closest('tr').attr('id'));
    });
    
    var updated_comment_ids = []
    var updated_comments = []
    $(table_id).find('.comment-updated').each(function () {
      updated_comment_ids.push($(this).closest('tr').attr('id'));
      updated_comments.push($(this).html());
    });

    var cookie = getCookie('csrftoken');
    $.ajax({
        url: "update_incident_status",
        method: 'POST',
        data: {normal: JSON.stringify(normal_ids), incident: JSON.stringify(incident_ids), viewed: JSON.stringify(viewed_ids),
              updated_comment_ids: JSON.stringify(updated_comment_ids), updated_comments: JSON.stringify(updated_comments)},
        headers: {'X-CSRFToken': cookie},
        success: function(response){
            $(alert_id).addClass('alert-success')
            $(alert_id).html(response)
        }
    });
    
    $(table_id).DataTable().draw();

});

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}


$('.new-constraint-column').change(function() {
    var type = $(this).find(":selected").data('type');
    var new_constraint_operator = $(this).parent().find('.new-constraint-operator')
    var new_constraint_value_div = $(this).parent().find('.new-constraint-value-div')
    populateConstraintOperators(type, new_constraint_operator)

    if (type == 'categorical') {
        new_constraint_value_div.html('<select class="form-control new-constraint-value"></select>')
        var new_constraint_value_input = new_constraint_value_div.find(".new-constraint-value")
        var distinct_values = $(this).find(":selected").data('distinct_values').split(',');
        populateValueSelector(distinct_values, new_constraint_value_input)
    } else {
        new_constraint_value_div.html('<input type="text" class="form-control new-constraint-value" placeholder="Value">')
    }

})

$(document).on('click', '.constraint', function(event) {
    event.preventDefault();
    $(this).remove();
})

$('.panel-heading').click(function() {
    $(this).parent().find('.panel-body').slideToggle();
})

$('.add-constraint-btn').click(function(event) {
    event.preventDefault();

    var column = $(this).parent().find('.new-constraint-column').find(':selected').val()
    var operator = $(this).parent().find('.new-constraint-operator').find(':selected').val()
    var data_type = $(this).parent().find('.new-constraint-column').find(':selected').data('type')
    if (data_type == "categorical") {
        var value = $(this).parent().find('.new-constraint-value').find(':selected').val()
    } else {
        var value = $(this).parent().find('.new-constraint-value').val()
    }

    if (column && operator && value) {
        $('<button>', {
            text: column + ' ' + operator + ' ' + value,
            class: 'constraint btn btn-info'
        }).appendTo($(this).parent().parent().find('.constraints')).data('column', column).data('operator', operator).data('value', value).data('data-type', data_type);
    }

})

$('.btn-clear-constraints').click(function(event) {
    event.preventDefault();

    $(this).parents().find('.constraints').html("");

})

$('.filter-btn').click(function(event) {
    event.preventDefault();
    
    if ($("ul#new-vs-history-selector li.active").attr('id') === "new-selector") {
        table_id = '#incident_table'
        alert_id = '#incident-alert'
    } else {
        table_id = '#history_table'
        alert_id = '#history-alert'
    }
    
    $(alert_id).html("");
    $(alert_id).removeClass('alert-danger')
    
    $(table_id).DataTable().draw()
})

function populateConstraintOperators(constraintType, new_constraint_operator) {
    var operators = [{'name': 'equal', 'value': '='}, {'name': 'not equal', 'value': '!='}];

    if (constraintType == 'numeric' || constraintType == 'date') {
        operators.push({'name': 'less than', 'value': '<'});
        operators.push({'name': 'greater than', 'value': '>'});
        operators.push({'name': 'less than or equal to', 'value': '<='});
        operators.push({'name': 'greater than or equal to', 'value': '>='});
    }
    var operatorSelection = new_constraint_operator.html("");
    for (var i = 0; i < operators.length; i++) {
        operatorSelection.append($('<option>', {
            value: operators[i].value,
            text: operators[i].name
        }));
    }

}

function populateValueSelector(distinct_values, new_constraint_value_input) {
   
    var values = [];
    for (var i = 0; i < distinct_values.length; i++) {
        values.push({'name': distinct_values[i], 'value': distinct_values[i]});
    }
    
    var new_constraint_selector = new_constraint_value_input.html("");
    for (var i = 0; i < values.length; i++) {
        new_constraint_selector.append($('<option>', {
            value: values[i].value,
            text: values[i].name
        }));
    }

}

function getConstraints(constraints_div) {
    var constraints = []
    constraints_div.find('button').each(function(i, button) {
        var button = $(button)
        constraints.push([button.data('column'), button.data('operator'), button.data('value'), button.data('data-type')])
    });
    return constraints;
}
