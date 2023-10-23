/*
 * The MIT License
 * Copyright (c) 2021- Nordic Institute for Interoperability Solutions (NIIS)
 * Copyright (c) 2017-2020 Estonian Information System Authority (RIA)
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 */

var API_ROOT = './api'

$('#new-constraint-column').change(function() {
    var type = $(this).find(":selected").data('type');
    populateConstraintOperators(type)
});

$(document).on('click', '.constraint', function(event) {
    event.preventDefault();
    $(this).remove();
});

$(document).on('click', '.order-clause', function(event) {
    event.preventDefault();
    $(this).remove();
});

$('.panel-heading').click(function() {
    $(this).parent().find('.panel-body').slideToggle();
});

$('#add-constraint-btn').click(function(event) {
    event.preventDefault();

    var column = $('#new-constraint-column').find(':selected').val()
    var operator = $('#new-constraint-operator').find(':selected').val()
    var value = $('#new-constraint-value').val()

    if (column && operator && value) {
        $('<button>', {
            text: column + ' ' + operator + ' ' + value,
            class: 'constraint btn btn-info'
        }).appendTo('#constraints').data('column', column).data('operator', operator).data('value', value);
    }

});

$('#add-order-clause-btn').click(function(event) {
    event.preventDefault();

    var column = $('#new-order-clause').find(':selected').val();
    var direction = $('#new-order-direction').find(':selected').val();

    if (column) {
        $('<button>', {
            text: column + ' ' + direction,
            class: 'order-clause btn btn-info'
        }).appendTo('#order-clauses').data('column', column).data('direction', direction);
    }
});

$('#download-meta-btn').click(function(event) {
    event.preventDefault();
    if (isInputValid()) {
        downloadMeta();
    }
});

$('#download-btn').click(function(event) {
    event.preventDefault();
    if (isInputValid()) {
        download();
    }
});

$('#preview-btn').click(function(event) {
    event.preventDefault();
    if (isInputValid()) {
        displayPreview();
    }
});

function isInputValid() {
    var date = $("#date").val();

    if (date === '') {
        $('.information-modal').modal('show');

        return false;
    }

    return true;
}

function populateConstraintOperators(constraintType) {
    var operators = [{'name': 'equal', 'value': '='}, {'name': 'not equal', 'value': '!='}];

    if (constraintType === 'numeric') {
        operators.push({'name': 'less than', 'value': '<'});
        operators.push({'name': 'greater than', 'value': '>'});
        operators.push({'name': 'less than or equal to', 'value': '<='});
        operators.push({'name': 'greater than or equal to', 'value': '>='});
    }

    var operatorSelection = $('#new-constraint-operator').html("");
    for (var i = 0; i < operators.length; i++) {
        operatorSelection.append($('<option>', {
            value: operators[i].value,
            text: operators[i].name
        }));
    }

}

function downloadMeta() {
    window.location = API_ROOT + '/daily_logs_meta' + getQuery();
}

function download() {
    window.location = API_ROOT + '/daily_logs' + getQuery();
}

function getQuery() {
    var date = escape($("#date").val());
    var columns = escape(JSON.stringify(getSelectedColumns()));
    var constraints = escape(JSON.stringify(getConstraints()));
    var orderClauses = escape(JSON.stringify(getOrderClauses()));

    return '?date=' + date + '&columns=' + columns + '&constraints=' + constraints + '&order-clauses=' + orderClauses;
}

function getSelectedColumns() {
    var radioValue = $('input[name=column-selection-type]:checked', '#download-form').val();
    if (radioValue === 'all') {
        return [];
    } else {
        var selectedColumns = [];
        $('#selected-columns :selected').each(function(i, selected){
            selectedColumns.push($(selected).val());
        });
        return selectedColumns;
    }
}

function getConstraints() {
    var constraints = [];
    $('#constraints').find('button').each(function(i, button) {
        var button = $(button);
        constraints.push({column: button.data('column'), operator: button.data('operator'), value: button.data('value')})
    });
    return constraints;
}

function getOrderClauses() {
    var orderClauses = [];
    $('#order-clauses').find('button').each(function(i, button) {
        var button = $(button);
        orderClauses.push({column: button.data('column'), order: button.data('direction')})
    });
    return orderClauses;
}

function displayPreview() {
    $('#datatable').html('');
    var columns = getSelectedColumns();

    var datatable = $('<table>').appendTo('#datatable').load('get_datatable_frame?columns=' + JSON.stringify(columns), function() {
        datatable.DataTable( {
            ajax: API_ROOT + '/logs_sample' + getQuery(),
            cache: false,
            scrollX: true,
            ordering: false,
            lengthChange: false,
            searching: false,
        } );
    })
}
