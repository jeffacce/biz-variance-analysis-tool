var pred = {};
var pred_csv = '';
var colID = 0;

var example_dfOld = `Brand,Subbrand,SKU,NR/HL,HL
a,ac,acg,20,25
a,ac,ach,25,5
a,ad,adi,40,10
a,ad,adj,50,100
b,be,bek,10,5
b,be,bel,20,5
b,bf,bfm,10,5
b,bf,bfn,20,50
`
var example_dfNew = `Brand,Subbrand,SKU,NR/HL,HL
a,ac,acg,20,50
a,ac,ach,30,50
a,ad,adi,40,50
a,ad,adj,50,50
b,be,bek,10,100
b,be,bel,10,100
b,bf,bfm,20,100
b,bf,bfn,20,100
`
// https://stackoverflow.com/questions/31128855/comparing-ecma6-sets-for-equality
// lol you have to roll your own set equality function in JS
function eqSet(as, bs) {
    if (as.size !== bs.size) return false;
    for (var a of as) if (!bs.has(a)) return false;
    return true;
}

function parseData(text) {
    var result = Papa.parse(text, config={'dynamicTyping': true, skipEmptyLines: true, 'header': true}).data;
    return result;
}


function generateOptions(pred) {
    var barWidth = "50%";
    var options = {
        tooltip : {
            trigger: 'axis',
            axisPointer : {
                type : 'shadow'
            },
            formatter: function (params) {
                var tar;
                if (params[1].value != '-') {
                    tar = params[1];
                }
                else {
                    tar = params[0];
                }
                return tar.name + '<br/>' + tar.seriesName + ' : ' + tar.value;
            }
        },
        legend: {
            data: ['Negative', 'Positive', 'Last Period', 'This Period']
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            containLabel: true
        },
        xAxis: {
            type : 'category',
            splitLine: {show:false},
            data : pred['xlabel'],
            offset: 10,
        },
        yAxis: {
            type : 'value',
        },
        series: [
            {
                name: 'Support',
                type: 'bar',
                stack: 'Total',
                itemStyle: {
                    normal: {
                        barBorderColor: 'rgba(0,0,0,0)',
                        color: 'rgba(0,0,0,0)'
                    },
                    emphasis: {
                        barBorderColor: 'rgba(0,0,0,0)',
                        color: 'rgba(0,0,0,0)'
                    }
                },
                data: pred['support'],
                barWidth: barWidth,
            },
            {
                name: 'Last Period',
                type: 'bar',
                stack: 'Total',
                label: {
                    normal: {
                        show: true,
                        position: 'top',
                    },
                },
                color: 'rgba(0,0,0,1)',
                data: pred['last'],
                barWidth: barWidth,
            },
            {
                name: 'This Period',
                type: 'bar',
                stack: 'Total',
                label: {
                    normal: {
                        show: true,
                        position: 'top',
                    },
                },
                color: 'rgba(0,0,128,1)',
                data: pred['this'],
                barWidth: barWidth,
            },
            {
                name: 'Positive',
                type: 'bar',
                stack: 'Total',
                label: {
                    normal: {
                        show: true,
                        position: 'top'
                    }
                },
                color: 'rgba(0,128,0,1)',
                data: pred['pos'],
                barWidth: barWidth,
            },
            {
                name: 'Negative',
                type: 'bar',
                stack: 'Total',
                label: {
                    normal: {
                        show: true,
                        position: 'bottom'
                    }
                },
                color: 'rgba(128, 0, 0, 1)',
                data: pred['neg'],
                barWidth: barWidth,
            }
        ]
    }
    return options;
}

function renderChart(pred) {
    var options = generateOptions(pred);
    myChart.setOption(options, true);
}

function parseColTypes() {
    var cols = $('#col-sel-group').find('li');
    var colNames = [];
    var colTypes = [];
    cols.each(function () {
        colNames.push($(this).find('h5').text());
        colTypes.push($(this).find('input:checked').val());
    })

    var idx_cols = [];
    var rate_col = '';
    var vol_col = '';
    for (let [i, elem] of colTypes.entries()) {
        switch (elem) {
            case 'idx':
                idx_cols.push(colNames[i]);
                break;
            case 'rate':
                rate_col = colNames[i];
                break;
            case 'vol':
                vol_col = colNames[i];
                break;
        }
    }

    return {
        'idx_cols': idx_cols,
        'rate_col': rate_col,
        'vol_col': vol_col,
    }
}

function generateRequest() {
    var dfOld = parseData($('#raw-data-old')[0].value);
    var dfNew = parseData($('#raw-data-new')[0].value);
    var mode = $(':radio[name=options-mode-radio]:checked').val();
    var round_digits = parseInt($('#options-mode-round-digits').val());

    checkValidity(dfOld, dfNew);
    colTypes = parseColTypes();
    var result = {
        'df_old': dfOld,
        'df_new': dfNew,
        'idx_cols': colTypes['idx_cols'],
        'rate_col': colTypes['rate_col'],
        'vol_col': colTypes['vol_col'],
        'mode': mode,
        'round_digits': round_digits,
    };
    return result;
}


function parseResponse(text) {
    return JSON.parse(text);
}


function disableSubmitButton() {
    $('#submit-button')[0].disabled = true;
    $("#spinner-running")[0].hidden = false;
}

function enableSubmitButton() {
    $('#submit-button')[0].disabled = false;
    $("#spinner-running")[0].hidden = true;
}

function disableDownloadButtons() {
    $('#download-csv-button')[0].disabled = true;
    $('#download-png-button')[0].disabled = true;
}

function enableDownloadButtons() {
    $('#download-csv-button')[0].disabled = false;
    $('#download-png-button')[0].disabled = false;
}


function sendRequest() {
    try {
        disableSubmitButton();
        disableDownloadButtons();
        var requestData = generateRequest();
        $.ajax('/variance-analysis/api/v1/raw', {
            data: JSON.stringify(requestData),
            contentType: "application/json; charset=utf-8",
            dataType: 'json',
            method: 'POST',
            success: (data, status, xhr) => {
                pred = data['waterfall'];
                pred_csv = Papa.unparse(data['raw']);
                warnings = data['warnings'];
                renderChart(pred);
                enableSubmitButton();
                enableDownloadButtons();
                if (warnings.length > 0) {
                    showError(warnings);
                }
            },
            error: (e) => {
                enableSubmitButton();
                disableDownloadButtons();
                showError('Oops! Something went wrong.');
            },
            timeout: 30000,
        });
    } catch (e) {
        showError(e);
        enableSubmitButton();
        disableDownloadButtons();
    }
}


function download(filename, text) {
    var element = document.createElement('a');
    element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(text));
    element.setAttribute('download', filename);

    element.style.display = 'none';
    document.body.appendChild(element);

    element.click();

    document.body.removeChild(element);
}


function loadFileAsText(fileToLoad, dest) {
    var fileReader = new FileReader();
    fileReader.onload = function() {
        $(dest)[0].value = fileReader.result;
        refreshColumns();
    }
    fileReader.readAsText(fileToLoad);
}

function addColumn(colname) {
    var listGroup = $('#col-sel-group');

    // construct a column card
    var li = $(`<li class="list-group-item card" id="col-${colID}-card">`);
    var title = $(`<h5 class="card-title"><i class="fas fa-bars mr-2"></i>${colname}</h5>`);
    var body = $(`
    <div class="card-body btn-group-toggle mt-2 p-0" data-toggle="buttons">
        Type:
    </div>
    `)
    var btnNA = $(`
    <label class="btn btn-outline-secondary active" id="col-${colID}-btn-na">
        <input type="radio" name="col-${colID}-radio-data-type" id="col-${colID}-radio-na" value="na" checked> N/A
    </label>
    `)
    var btnRate = $(`
    <label class="btn btn-outline-primary" id="col-${colID}-btn-rate">
        <input type="radio" name="col-${colID}-radio-data-type" id="col-${colID}-radio-rate" value="rate"> Rate
    </label>
    `)
    var btnIdx = $(`
    <label class="btn btn-outline-info" id="col-${colID}-btn-idx">
        <input type="radio" name="col-${colID}-radio-data-type" id="col-${colID}-radio-idx" value="idx"> Mix
    </label>
    `)
    var btnVol = $(`
    <label class="btn btn-outline-success" id="col-${colID}-btn-vol">
        <input type="radio" name="col-${colID}-radio-data-type" id="col-${colID}-radio-vol" value="vol"> Volume
    </label>
    `)

    body.append(btnNA, btnRate, btnIdx, btnVol);
    body.find(`[name=col-${colID}-radio-data-type]`).on('change', dataTypeRadioCallback);
    li.append(title, body);
    listGroup.append(li);
    colID++;

    return li;
}

function refreshColumns() {
    // optimization opportunity:
    // data is parsed twice (once for request, once for refresh column)
    var dfOld = parseData($('#raw-data-old')[0].value);
    var dfNew = parseData($('#raw-data-new')[0].value);
    var dfOldCols = Object.keys(dfOld[0]);
    var dfNewCols = Object.keys(dfNew[0]);

    var cols = [];  // avoiding sets to preserve order; there's probably a better way to do this
    for (let [i, elem] of dfOldCols.entries()) {
        if (dfNewCols.includes(elem) & !(cols.includes(elem))) {
            cols.push(elem);
        }
    }
    for (let [i, elem] of dfNewCols.entries()) {
        if (dfOldCols.includes(elem) & !(cols.includes(elem))) {
            cols.push(elem);
        }
    }

    var currentColSet = new Set($('#col-sel-group').find('h5').map(function() {return this.innerText}));
    var colSet = new Set(cols);

    // if two sets are not equal, update the columns
    if (!eqSet(currentColSet, colSet)) {
        // empty current col list
        $('#col-sel-group').empty();
        colID = 0;
        for (let [i, elem] of cols.entries()) {
            addColumn(elem);
        }
    }
}

function dataTypeRadioCallback() {
    var colCard = $(this).closest('li');
    var otherCols = $('#col-sel-group').find(`:radio[value=${this.value}]:checked`).not(this);

    if (this.value == 'rate') {
        // there can only be one rate column
        otherCols.closest('.btn-group-toggle').find(':radio[value=na]').click();
        // move rate column to the start of the list
        if (colCard.index() != 0) {
            colCard.slideUp(200, () => {
                colCard.detach();
                $('#col-sel-group').prepend(colCard);
                colCard.slideDown(200);
            });
        }
        // disable sorting for this element, set bg-light color visual cue
        // ('.bg-light' used by SortableJS filter as unsortable)
        colCard.addClass('bg-light');
        colCard.find('i').hide();
    }
    if (this.value == 'vol') {
        // there can only be one volume column
        otherCols.closest('.btn-group-toggle').find(':radio[value=na]').click();
        // move volume column to the end of the list
        if (!(colCard.index() == colCard.siblings().length)) {
            // not at the end; play animation and move
            colCard.slideUp(200, () => {
                colCard.detach();
                $('#col-sel-group').append(colCard);
                colCard.slideDown(200);
            });
        }
        colCard.addClass('bg-light');
        colCard.find('i').hide();
    }
    if ((this.value == 'na') | (this.value == 'idx')) {
        // enable sorting for this element, remove bg-light color visual cue
        // ('.bg-light' used by SortableJS filter as unsortable)
        colCard.removeClass('bg-light');
        colCard.find('i').show();
    }
}

function showError(msg = 'Oops! Something went wrong.') {
    $('#modal-err-msg-body').text(msg);
    $('#modal-err-msg').modal();
}

function checkValidity(dfOld, dfNew) {
    if ($('#raw-data-old')[0].value.length == 0) {
        $('#nav-data-old-tab').click();
        throw "Missing: last period data."
    }
    if ($('#raw-data-new')[0].value.length == 0) {
        $('#nav-data-new-tab').click();
        throw "Missing: this period data."
    }
    var colTypes = parseColTypes();
    if ((colTypes['rate_col'] == '') & (colTypes['vol_col'] == '') & (colTypes['idx_cols'].length == 0)) {
        refreshColumns();
        $('#nav-options-tab').click();
        throw 'Please select column types in Options. Drag to reorder the columns.';
    }
    if (colTypes['rate_col'] == '') {
        $('#nav-options-tab').click();
        throw "Please specify the rate column."
    }
    if (colTypes['vol_col'] == '') {
        $('#nav-options-tab').click();
        throw "Please specify the volume column."
    }
    return true;
}

$('#raw-data-old-file-input').change(() => {
    var fileToRead = $("#raw-data-old-file-input")[0].files[0];
    loadFileAsText(fileToRead, '#raw-data-old');
});

$('#raw-data-new-file-input').change(() => {
    var fileToRead = $("#raw-data-new-file-input")[0].files[0];
    loadFileAsText(fileToRead, '#raw-data-new');
});

$('#submit-button').on('click', () => {
    sendRequest();
});

$('#download-csv-button').on('click', () => {
    download('Waterfall Data.csv', pred_csv);
});

$("#download-png-button").click(() => {
    var a = document.createElement("a");
    a.href = myChart.getDataURL();
    a.download = "Waterfall Chart.png";
    a.click();
})

$('#fill-example-data-old-button').on('click', () => {
    $('#raw-data-old').val(example_dfOld);
    refreshColumns();
})
$('#fill-example-data-new-button').on('click', () => {
    $('#raw-data-new').val(example_dfNew);
    refreshColumns();
})

$('#refresh-col-button').click(refreshColumns);
$('[data-toggle="tooltip"]').tooltip({trigger: 'hover'});  // init all tooltips

var chartContainer = $('#chart-container')[0];
var myChart = echarts.init(chartContainer);
var cols = new Sortable(
    $('#col-sel-group')[0],
    {
        animation: 150,
        ghostClass: 'bg-secondary',
        dragClass: 'bg-light',
        filter: '.bg-light',
    }
);

$(document).bind('keydown', function(e) {
    if (e.shiftKey & (e.key == 'Enter')) {
        sendRequest();
    }
})
