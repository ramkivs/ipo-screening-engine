"use strict";

function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }

function _possibleConstructorReturn(self, call) { if (!self) { throw new ReferenceError("this hasn't been initialised - super() hasn't been called"); } return call && (typeof call === "object" || typeof call === "function") ? call : self; }

function _inherits(subClass, superClass) { if (typeof superClass !== "function" && superClass !== null) { throw new TypeError("Super expression must either be null or a function, not " + typeof superClass); } subClass.prototype = Object.create(superClass && superClass.prototype, { constructor: { value: subClass, enumerable: false, writable: true, configurable: true } }); if (superClass) Object.setPrototypeOf ? Object.setPrototypeOf(subClass, superClass) : subClass.__proto__ = superClass; }

var stringToHTML = function stringToHTML(str) {
  var parser = new DOMParser();
  var doc = parser.parseFromString(str, "text/html");
  var value = doc.body;
  var val = value.innerHTML || "";
  if (val.indexOf("href=") >= 0) {
    var anchortag = value.getElementsByTagName("a")[0] || "";
    val = a({ href: anchortag.href, target: "_blank" }, anchortag.innerText);
  }
  return val;
};

var IPOTable = function (_BlinkElement) {
  _inherits(IPOTable, _BlinkElement);

  function IPOTable(args) {
    _classCallCheck(this, IPOTable);

    var _this = _possibleConstructorReturn(this, _BlinkElement.call(this));

    var attr = B.extractArgAttrs(args);
    _this.state = new B.State({
      row: attr.row,
      data: attr.data || []
    });

    var data = _this.state.data || [];

    function format(val) {
      var readmore = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : false;

      if (parseFloat(val) || parseFloat(val) === 0) {
        return td({ class: "text-align-right" }, DecimalFixed(val).toString());
      }
      return td(readmore ? convertToReadMore(val) : val);
    }

    var seriesData = [];
    data.series && data.series.forEach(function (d, index) {
      seriesData.push(tr(td(d.value)));
    });

    var infoTable = [];
    data.dataList && data.dataList.forEach(function (d, index) {
      // if (index === 0) {
      //   infoTable.push(
      //     tr(th({ colspan: 2, class: "text-center" }, d.title || ""))
      //   );
      // } else {
      infoTable.push(tr(th(d.title || ""), d.value && d.value.indexOf(".zip") >= 0 ? td({}, a({ href: d.value == null ? "" : d.value, target: "_blank", title: "Zip" }, img({
        src: "/assets/images/icon-zip.svg",
        height: "17",
        width: "14",
        alt: "download " + d.title + " attachment",
        title: "zip"
      }), " download")) : d.title === 'Symbol' ? td(d.value || "") : td(stringToHTML(d.value) || "")));
      // }
    });
    var getLeftTable = function getLeftTable() {
      return div({ class: "table-wrap" }, table({ class: "w-100 common_table table-bordered" }, tbody(concatArr([{}], infoTable || ""))));
    };
    /*let getLeftTable = () => {
            return div({class:'table-wrap'}, table({class : 'w-100 common_table table-bordered'},
                tbody(
                    tr(
                        th({width : '30%'},'Sybmol'),
                        td(data.symbol || ""),
                    ),
                    tr(
                        th('Series'),
                        td({class:'p-0'},
                            table({class : 'w-100 common_table alt_row'},tbody(
                                concatArr([{}], seriesData || "")
                            ))
                        )
                    ),
                    tr(
                        th('Issue Period '),
                        td(data.issuePeriod || "")
                    ),
                    tr(
                        th('Post Issue Modification Period'),
                        td(data.modificationDate || "")
                    ),
                )
            ))
        };*/

    var dom = div({}, getLeftTable());

    //mandatory code for a BlinkUI component
    _this.args = dom.args;
    _this.elem = dom.elem;
    _this.elem.cmp = _this;
    //mandatory code for a BlinkUI component ends
    return _this;
  }

  return IPOTable;
}(BlinkElement);

instantiate("IPOTable", IPOTable);

var IPOLwfTable = function (_BlinkElement2) {
  _inherits(IPOLwfTable, _BlinkElement2);

  function IPOLwfTable(args) {
    _classCallCheck(this, IPOLwfTable);

    var _this2 = _possibleConstructorReturn(this, _BlinkElement2.call(this));

    var attr = B.extractArgAttrs(args);
    _this2.state = new B.State({
      data: attr.data || []
    });

    var dataList = _this2.state.data || [];
    if (!Array.isArray(dataList) || dataList.length === 0) {
      var _ret;

      return _ret = div("No data available"), _possibleConstructorReturn(_this2, _ret);
    }

    // Extract first object from issueInfo array
    var data = dataList[0];

    // Define readable labels for each key
    var fieldLabels = {
      symbol: "Symbol",
      issuePeriod: "Issue Period",
      issueSize: "Issue Size",
      offerType: "Offer Type",
      issueType: "Issue Type",
      redemptionPrice: "Redemption Price",
      faceValue: "Face Value",
      marketTimings: "Market Timings",
      offerDocument: "Offer Document"
    };

    // Build table rows dynamically
    var infoTable = [];
    Object.keys(fieldLabels).forEach(function (key) {
      var label = fieldLabels[key];
      var value = data[key];

      if (!value) return; // skip missing keys

      // If .zip file, show download link
      if (value.indexOf(".zip") >= 0) {
        infoTable.push(tr(th(label), td({}, a({
          href: value,
          target: "_blank",
          title: "Download attachment"
        }, img({
          src: "/assets/images/icon-zip.svg",
          height: "17",
          width: "14",
          alt: "download " + label + " attachment"
        }), " download"))));
      } else {
        infoTable.push(tr(th(label), td(value)));
      }
    });

    // Table wrapper
    var getTable = function getTable() {
      return div({ class: "table-wrap" }, table({ class: "w-100 common_table table-bordered" }, tbody(infoTable)));
    };

    var dom = div({}, getTable());

    // mandatory Blink UI boilerplate
    _this2.args = dom.args;
    _this2.elem = dom.elem;
    _this2.elem.cmp = _this2;
    return _this2;
  }

  return IPOLwfTable;
}(BlinkElement);

instantiate("IPOLwfTable", IPOLwfTable);

var DemandGraphTable = function (_BlinkElement3) {
  _inherits(DemandGraphTable, _BlinkElement3);

  function DemandGraphTable(args) {
    _classCallCheck(this, DemandGraphTable);

    var _this3 = _possibleConstructorReturn(this, _BlinkElement3.call(this));

    var attr = B.extractArgAttrs(args);
    _this3.state = new B.State({
      row: attr.row,
      data: attr.data || [],
      series: attr.series || false,
      bid: attr.bid || false
    });

    var data = _this3.state.data;

    function format(val) {
      var readmore = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : false;

      if (parseFloat(val) || parseFloat(val) === 0) {
        return td({ class: "text-align-right" }, DecimalFixed(val).toString());
      }
      return td(readmore ? convertToReadMore(val) : val);
    }

    var getTable = function getTable() {
      return table({ class: "w-100 common_table table-bordered" }, tbody(tr(td("Total Issue Size"), td({ class: "text-right" }, DecimalFixed(data.totalIssueSize || "", true))), tr(td("Total Bids Received"), td({ class: "text-right" }, DecimalFixed(data.totalBidRecieved || "", true))), seriesType != "DEBT" ? tr(td("Total Bids Received at Cut-off price"), td({ class: "text-right" }, DecimalFixed(data.totalBidAtCutOff || "0.00", true))) : "", tr(td("No. of times issue is subscribed"), td({ class: "text-right" }, seriesType == "DEBT" ? Number(data.noOfTimeSuscribed) > 0 ? DecimalFixed(data.noOfTimeSuscribed, false) : "0.00" : Number(data.noOfTimesIssueSubscribed) > 0 ? DecimalFixed(data.noOfTimesIssueSubscribed, false) : "0.00"))));
    };

    var getSeriesTable = function getSeriesTable() {
      if (data.seriesMap) {
        var seriesData = [];
        seriesData.push(td({ class: "text-right bold" }, "Series"));
        data.seriesMap && data.seriesMap.forEach(function (d, index) {
          seriesData.push(td({ class: "text-right bold" }, d.type));
        });
        var seriesQuantity = [];
        seriesQuantity.push(td({ class: "text-right" }, "Quantity"));
        data.seriesMap && data.seriesMap.forEach(function (d, index) {
          seriesQuantity.push(td({ class: "text-right" }, d.value ? d.value.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",") : ""));
        });

        return table({ class: "w-100 common_table table-bordered" }, tbody(tr(concatArr([{}], seriesData || "")), tr(concatArr([{}], seriesQuantity || ""))));
      }
    };

    var getBidTable = function getBidTable() {
      if (data) {
        var priceData = [];
        var shareQuantity = [];
        priceData.push(td({ class: "text-right bold" }, "Price >="));
        shareQuantity.push(td({ class: "text-right" }, "No of Share(in Lakh)"));

        for (var _iterator = Object.entries(data), _isArray = Array.isArray(_iterator), _i = 0, _iterator = _isArray ? _iterator : _iterator[Symbol.iterator]();;) {
          var _ref;

          if (_isArray) {
            if (_i >= _iterator.length) break;
            _ref = _iterator[_i++];
          } else {
            _i = _iterator.next();
            if (_i.done) break;
            _ref = _i.value;
          }

          var _ref2 = _ref,
              key = _ref2[0],
              value = _ref2[1];

          priceData.push(td({ class: "text-right bold" }, key || "-"));
          shareQuantity.push(td({ class: "text-right" }, value || "-"));
        }

        return table({ class: "w-100 common_table table-bordered" }, tbody(tr(concatArr([{}], priceData || "")), tr(concatArr([{}], shareQuantity || ""))));
      }
    };

    var dom = div({ class: "table-wrap mt-3" }, _this3.state.bid ? getBidTable() : _this3.state.series ? getSeriesTable() : getTable());

    //mandatory code for a BlinkUI component
    _this3.args = dom.args;
    _this3.elem = dom.elem;
    _this3.elem.cmp = _this3;
    //mandatory code for a BlinkUI component ends
    return _this3;
  }

  return DemandGraphTable;
}(BlinkElement);

instantiate("DemandGraphTable", DemandGraphTable);

var apiData = void 0;
var seriesType = void 0;
var companyClarificationURL = void 0;
var apiDataOld = [{
  issueInformation: [{
    symbol: "IIFLFIN",
    series: [{
      value: "S1 - 10.75% Tenor 26 months, for category I, II, III & IV Investors - Annual Option"
    }, {
      value: "S1 - 10.75% Tenor 26 months, for category I, II, III & IV Investors - Annual Option"
    }, {
      value: "S1 - 10.75% Tenor 26 months, for category I, II, III & IV Investors - Annual Option"
    }, {
      value: "S1 - 10.75% Tenor 26 months, for category I, II, III & IV Investors - Annual Option"
    }, {
      value: "S1 - 10.75% Tenor 26 months, for category I, II, III & IV Investors - Annual Option"
    }],
    issuePeriod: "04-Feb-2019 to 04-Mar-2019",
    modificationDate: "05-Mar-2019 (10:00 AM to 1:00 PM)"
  }],
  bidDetails: [{
    srNo: "1",
    category: "Qualified Institutional Buyers(QIBs)",
    noOfSharesOffered: "0",
    noOfsharesBid: "0",
    noOfTime: "0.00"
  }],
  nseDemand: [{
    noOfSharesOffered: "0",
    noOfsharesBid: "0",
    noOfTime: "0.00",
    series: [{
      type: "S1",
      value: "1271"
    }, {
      type: "S2",
      value: "1957"
    }, {
      type: "S3",
      value: "3555"
    }, {
      type: "S4",
      value: "1271"
    }, {
      type: "S5",
      value: "230"
    }, {
      type: "S6",
      value: "90"
    }]
  }],
  nseBseDemand: [{
    noOfSharesOffered: "0",
    noOfsharesBid: "0",
    noOfTime: "0.00",
    series: [{
      type: "S1",
      value: "1271"
    }, {
      type: "S2",
      value: "1957"
    }, {
      type: "S3",
      value: "3555"
    }, {
      type: "S4",
      value: "1271"
    }, {
      type: "S5",
      value: "230"
    }, {
      type: "S6",
      value: "90"
    }]
  }],
  company: "India Infoline Finance Ltd",
  type: "Current Issue"
}];

var loadIssueInformation = function loadIssueInformation() {
  try {
    var issueInfo = IPOTable({ data: apiData.issueInfo });
    B.render(issueInfo, B.findOne("#issueInfo"));
  } catch (e) {
    console.log(e);
  }
};

var loadIssueInformationLwf = function loadIssueInformationLwf() {
  try {
    var issueInfo = IPOLwfTable({ data: apiData.issueInfo });
    B.render(issueInfo, B.findOne("#issueInfo"));
  } catch (e) {
    console.log(e);
  }
};

function BidRefresh() {
  try {
    var url = window.location.href;
    // url = removeURLParameter(url, "symbol");
    // url = removeURLParameter(url, "tabIndex");
    window.location.href = url;
  } catch (e) {
    console.log(e);
  }
}
var loadBidDetails = function loadBidDetails(symbol, series, type) {
  try {
    //let jsonUrl = "/json/liveMarket/issue-information-bid.json";
    var jsonUrl = "/json/liveMarket/issue-information-nse-bid.json";
    var last_row_bold = 'last_row_bold';
    if (series.toString().toLowerCase() === "eq") {
      jsonUrl = "/json/liveMarket/issue-information-bid.json";
    } else if (series.toString().toLowerCase() === "sme") {
      jsonUrl = "/json/liveMarket/issue-information-bid-sme.json";
    } else if (series.toString().toLowerCase() === "rr") {
      jsonUrl = "/json/liveMarket/issue-information-bid-consolidated-rr.json";
    } else if (series.toString().toLowerCase() === "iv") {
      jsonUrl = "/json/liveMarket/issue-information-nse-bid-iv.json";
    } else if (series.toString().toLowerCase() === "debt") {
      jsonUrl = "/json/liveMarket/issue-information-bid-details.json";
      last_row_bold = '';
    }
    B.get(jsonUrl).then(function (resp) {
      var respJSONObj = JSON.parse(resp);
      var publicIssuesBid = customTable({
        tableStyle: {
          id: "publicIssuesBidTable",
          class: "w-100 common_table table-bordered alt_row " + last_row_bold
        },
        colData: respJSONObj.columns || [],
        rowData: []
      });
      $("#publicIssuesBidTable").empty();
      B.render(publicIssuesBid, B.findOne("#publicIssuesBid"));

      B.findOne("#publicIssuesBidTable .emptyRow").innerHTML = loader;
      var vrdUrls = [];

      B.get("/api/ipo-bid-details?symbol=" + encodeURIComponent(symbol) + "&series=" + series).then(function (resp) {
        var respJSON = JSON.parse(resp);
        var noOfShareBidFor = void 0;
        if (respJSON && respJSON.data && respJSON.data instanceof Array) {
          respJSON.data.slice(1).forEach(function (d) {
            if (d && d.noOfshareBid) {
              noOfShareBidFor = d.noOfshareBid.replace(/\,+/g, "");
            } else {
              noOfShareBidFor = d.noOfsharesBid.replace(/\,+/g, "");
            }
            vrdUrls.push({
              srNo: d.srNo,
              //category must me italic if series no. matches the pattern 1(a)
              category: series.toString().toLowerCase() === 'eq' || series.toString().toLowerCase() === 'sme' ? convertToItalic(d, 'category') : d.category,
              noofapplication: d.noofapplication,
              noOfSharesOffered: d.noOfSharesOffered && d.noOfSharesOffered.replace(/\,+/g, ""),
              noOfsharesBid: noOfShareBidFor,
              // noOfShareBidFor,
              // noOfsharesBid:d.noOfsharesBid && d.noOfsharesBid.replace(/\,+/g, ""),
              // noOfsharesBid: d && d.noOfsharesBid ? d.noOfsharesBid.replace(/\,+/g, ""): d && d.noOfshareBid ? d.noOfshareBid.replace(/\,+/g, ""):"",
              noOfTime: d.noOfTime && d.noOfTime.replace(/\,+/g, "")
              //d.noOfTime && d.noOfTime.replace(/\,+/g, "")
            });
          });
          publicIssuesBid.state.rowData = vrdUrls;
        } else {
          publicIssuesBid.state.rowData = [];
        }
        $("#publicIssuesBidWrapper .asondate").text(respJSON.updateTime === 'Updated as on null' ? '-' : respJSON.updateTime);
      });
    });
  } catch (e) {
    console.log(e);
  }
};

var loadConBidDetails = function loadConBidDetails(symbol, series, type) {
  try {
    //let jsonUrl = "/json/liveMarket/issue-information-bid.json";
    var jsonUrl = "/json/liveMarket/issue-information-bid-consolidated.json";
    var last_row_bold = 'last_row_bold';

    if (series.toString().toLowerCase() === "eq") {
      jsonUrl = "/json/liveMarket/issue-information-bid-consolidated-eq.json";
    } else if (series.toString().toLowerCase() === "sme") {
      jsonUrl = "/json/liveMarket/issue-information-bid-sme-con.json";
    } else if (series.toString().toLowerCase() === "debt") {
      jsonUrl = "/json/liveMarket/issue-information-bid-details.json";
      last_row_bold = '';
    }
    B.get(jsonUrl).then(function (resp) {
      var respJSONObj = JSON.parse(resp);
      var publicIssuesBidConsolidated = customTable({
        tableStyle: {
          id: "publicIssuesBidConsolidatedTable",
          class: "w-100 common_table table-bordered alt_row " + last_row_bold
        },
        colData: respJSONObj.columns || [],
        rowData: []
      });
      $("#publicIssuesBidConsolidatedTable").empty();
      B.render(publicIssuesBidConsolidated, B.findOne("#publicIssuesBidConsolidated"));

      B.findOne("#publicIssuesBidConsolidatedTable .emptyRow").innerHTML = loader;

      B.get("/api/ipo-active-category?symbol=" + encodeURIComponent(symbol)).then(function (resp) {
        var respJSON = JSON.parse(resp);
        if (respJSON.dataList && respJSON.dataList.length > 0) {
          try {
            publicIssuesBidConsolidated.state.rowData = respJSON.dataList.slice(1);
            publicIssuesBidConsolidated.state.rowData = publicIssuesBidConsolidated.state.rowData.map(function (r) {
              //category must me italic if series no. matches the pattern 1(a)
              r.category = series.toString().toLowerCase() === 'eq' || series.toString().toLowerCase() === 'sme' ? convertToItalic(r, 'category') : r.category;
              return r;
            });
          } catch (error) {
            console.error(error);
          }
        } else {
          publicIssuesBidConsolidated.st;
        }
        $("#publicIssuesBidConsolidatedWrapper .asondate").text(respJSON.updateTime === "Updated as on null" ? '-' : respJSON.updateTime);
      });
    });
  } catch (e) {
    console.log(e);
  }
};

var loadNseDemandGraph = function loadNseDemandGraph(data) {
  try {
    var nseDemandGraph = DemandGraphTable({ data: data, series: false });
    B.render(nseDemandGraph, B.findOne("#nseDemandGraph"));
  } catch (e) {
    console.log(e);
  }
};

var loadNseDemandGraphSeries = function loadNseDemandGraphSeries(data) {
  try {
    var nseDemandGraphSeries = DemandGraphTable({ data: data, series: true });
    B.render(nseDemandGraphSeries, B.findOne("#nseDemandGraphSeries"));
  } catch (e) {
    console.log(e);
  }
};

var loadNseDemandGraphBid = function loadNseDemandGraphBid(data) {
  try {
    var nseDemandGraphBid = DemandGraphTable({ data: data, bid: true });
    B.render(nseDemandGraphBid, B.findOne("#nseDemandGraphSeries"));
  } catch (e) {
    console.log(e);
  }
};

var moveIndexPositionOfArr = function moveIndexPositionOfArr(arr, old_index, new_index) {
  if (new_index >= arr.length) {
    var k = new_index - arr.length + 1;
    while (k--) {
      arr.push(undefined);
    }
  }
  arr.splice(new_index, 0, arr.splice(old_index, 1)[0]);
  return arr;
};

var loadNseGraph = function loadNseGraph(data, type) {
  try {
    var chartData = [];
    if (type === "series") {

      for (var i = 0; i < data.length; i++) {
        chartData.push([data[i].type, parseInt(data[i].value)]);
      }

      // data.forEach((d,index) => {
      //   console.log(d,"-=-index==",index)
      //   chartData.push([d.type, parseInt(d.value)]);

      // });
    }
    if (type === "plot") {
      for (var _iterator2 = Object.entries(data), _isArray2 = Array.isArray(_iterator2), _i2 = 0, _iterator2 = _isArray2 ? _iterator2 : _iterator2[Symbol.iterator]();;) {
        var _ref3;

        if (_isArray2) {
          if (_i2 >= _iterator2.length) break;
          _ref3 = _iterator2[_i2++];
        } else {
          _i2 = _iterator2.next();
          if (_i2.done) break;
          _ref3 = _i2.value;
        }

        var _ref4 = _ref3,
            key = _ref4[0],
            value = _ref4[1];

        var val = typeof value === "string" ? value.replace(/,/g, "") : value;
        var keys = key == "Cut-Off" ? "Cut-Off" : parseFloat(key).toFixed(2);

        chartData.push([keys, parseInt(val)]);
      }
    }
    // const data_chart = moveIndexPositionOfArr(
    //   chartData,
    //   chartData.length - 1,
    //   0
    // );
    Highcharts.setOptions({
      lang: {
        numericSymbols: null,
        thousandsSep: ","
      }
    });

    Highcharts.chart("nseGraph", {
      chart: {
        type: "column"
      },
      title: "",
      xAxis: {
        type: "category"
        // labels: {
        //   rotation: 0,
        // },
      },
      yAxis: {
        min: 0,
        title: {
          text: "Demand Data (in Lakhs)"
        }
      },
      credits: {
        enabled: false
      },
      legend: {
        enabled: false
      },
      tooltip: {
        pointFormat: "Demand Data: <b>{point.y} Lakhs</b>"
      },
      series: [{
        name: "Cumulative Bids",
        data: chartData,
        dataLabels: {
          enabled: true,
          rotation: -90,
          color: "#FFFFFF",
          align: "right",
          style: {
            fontSize: "12px",
            textOutline: "0px"
          },
          //format: "{point.y}", // one decimal
          y: 100 // 10 pixels down from the top
          // x: -10
        }
      }]
    });
  } catch (e) {
    console.log(e);
  }
};

var loadNseBseDemandGraph = function loadNseBseDemandGraph() {
  try {
    var nseBseDemandGraph = DemandGraphTable({
      data: apiDataOld[0].nseBseDemand,
      series: false
    });
    B.render(nseBseDemandGraph, B.findOne("#nseBseDemandGraph"));
  } catch (e) {
    console.log(e);
  }
};

var loadNseBseDemandGraphSeries = function loadNseBseDemandGraphSeries() {
  try {
    var nseBseDemandGraphSeries = DemandGraphTable({
      data: apiDataOld[0].nseBseDemand,
      series: true
    });
    B.render(nseBseDemandGraphSeries, B.findOne("#nseBseDemandGraphSeries"));
  } catch (e) {
    console.log(e);
  }
};

var loadNseBseGraph = function loadNseBseGraph() {
  try {
    var chartData = [];
    apiData[0].nseBseDemand[0].series.forEach(function (d) {
      chartData.push([d.type, parseInt(d.value)]);
    });
    Highcharts.chart("nseBseGraph", {
      chart: {
        type: "column"
      },
      title: "",
      xAxis: {
        type: "category",
        labels: {
          rotation: -45
        } // one decimal
      },
      yAxis: {
        min: 0,
        title: {
          text: "Demand Data (in Lakhs)"
        }
      },
      credits: {
        enabled: false
      },
      legend: {
        enabled: false
      },
      tooltip: {
        pointFormat: "Demand Data: <b>{point.y} Lakhs</b>"
      },
      series: [{
        name: "Cumulative Bids",
        data: chartData,
        dataLabels: {
          enabled: true,
          rotation: -90,
          color: "#FFFFFF",
          align: "right",
          //format: "{point.y}", // one decimal
          y: 10 // 10 pixels down from the top
        }
      }]
    });
  } catch (e) {
    console.log(e);
  }
};

var loadDemandData = function loadDemandData(symbol) {
  var series = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : 'EQ';

  try {
    B.get("/json/liveMarket/issue-information-demand.json").then(function (resp) {
      var respJSONObj = JSON.parse(resp);
      var issuesInfoNseDemand = customTable({
        tableStyle: {
          id: "nseBidDataTable",
          class: "w-100 common_table table-bordered alt_row"
        },
        colData: respJSONObj.columns || [],
        rowData: []
      });
      $("#nseBidDataTable").empty();
      B.render(issuesInfoNseDemand, B.findOne("#nseBidData"));

      B.findOne("#nseBidDataTable .emptyRow").innerHTML = loader;

      B.get("/api/ipo-chart-demand?symbol=" + encodeURIComponent(symbol) + "&exchange=NSE").then(function (resp) {
        try {
          var respJSON = JSON.parse(resp);
          issuesInfoNseDemand.state.rowData = respJSON || [];
          B.findOne("#nseBidDataTimeStamp").innerHTML = respJSON.length === 0 ? '-' : "Updated As on " + respJSON && respJSON[0].timestamp;
        } catch (e) {
          console.log(e.message);
        }
      });

      var issuesInfoExchangeDemand = customTable({
        tableStyle: {
          id: "exchangeBidDataTable",
          class: "w-100 common_table table-bordered alt_row"
        },
        colData: respJSONObj.columns || [],
        rowData: []
      });
      $("#exchangeBidDataTable").empty();
      B.render(issuesInfoExchangeDemand, B.findOne("#exchangeBidData"));
      B.findOne("#exchangeBidDataTable .emptyRow").innerHTML = loader;

      B.get("/api/ipo-chart-demand?symbol=" + encodeURIComponent(symbol) + "&exchange=ALL").then(function (resp) {
        try {
          if (series.toString().toLowerCase() === "sme") {
            $("#allXchngBidTable").hide();
          }
          var respJSON = JSON.parse(resp);
          issuesInfoExchangeDemand.state.rowData = respJSON || [];
          B.findOne("#allExchangeBidDataTimeStamp").innerHTML = respJSON.length === 0 ? '-' : "Updated As on " + respJSON && respJSON[0].timestamp;
        } catch (e) {
          console.log(e.message);
        }
      });
    });
  } catch (e) {
    console.log(e);
  }
};

var loadAPIData = function loadAPIData(symbol, series, type, appType, category) {
  try {

    if (series === 'EQ' || series === 'SME') {
      disclaimerNote();
      disclaimerNoteDg();
    }
    // /api/ipo-detail?symbol=JDIAL&series=EQ -- Issue Information
    // /api/ipo-detail?symbol=IRFCT2&series=DEBT   ---  Demand Graph
    // /api/ipo-detail?symbol=INDIAMART&series=EQ  --- Demand Data last tab
    var uri = void 0;
    if (typeof symbol === "undefined" || symbol === null) {
      alert("Symbol Missing !!! Unable to fetch data");
      return;
    }
    if (typeof symbol !== "undefined" && symbol !== null && typeof series !== "undefined" && series !== null) {
      uri = "/api/ipo-detail?symbol=" + encodeURIComponent(symbol) + "&series=" + series;
    } else if (appType) {
      if (appType == "rights") {
        uri = "/api/ipo-detail-rights?symbol=" + encodeURIComponent(symbol) + "&appType=" + appType;
      } else {
        uri = "/api/ipo-detail?symbol=" + encodeURIComponent(symbol) + "&appType=" + appType;
      }
    } else {
      uri = "/api/ipo-detail?symbol=" + encodeURIComponent(symbol);
    }

    B.get(uri).then(function (resp) {
      apiData = JSON.parse(resp);

      // console.log('apiData', apiData);
      if (companyClarificationURL) {
        if (apiData && apiData.issueInfo && 'dataList' in apiData.issueInfo && apiData.issueInfo.dataList.length > 0) {
          apiData.issueInfo.dataList.push({ title: "Company Clarification", value: "<a href=\"" + companyClarificationURL + "\" download>Company Clarification</a>" });
        }
      }
      // const timestampAll2=apiData.demandGraph.TIMESTAMP == undefined? "Updated " + apiData.demandGraph.timestamp || "": "Updated " + apiData.demandGraph.TIMESTAMP || ""
      // $("#demandGraphTimestamp").text(
      //    timestampAll2
      //   );

      if (apiData.demandGraph && apiData.demandGraph.TIMESTAMP != undefined) {
        $("#demandGraphTimestamp").text("Updated " + apiData.demandGraph.TIMESTAMP);
      } else if (apiData.demandGraph && apiData.demandGraph.timestamp != undefined) {
        $("#demandGraphTimestamp").text("Updated " + apiData.demandGraph.timestamp);
      } else {
        $("#demandGraphTimestamp").text("");
      }

      $("#issueType").text(type || "IPO type");

      if (type != 'Forthcoming' && apiData.activeCat) {
        $("#companyName").text(apiData.activeCat.heading || apiData.companyName || "Company Name");
      } else {
        $("#companyName").text('');
      }

      // console.log('further processing before if');
      if (type && type.toLowerCase() === "forthcoming" || appType) {
        loadIssueInformation();
        $("#issueInfoTab li").eq(0).siblings().remove();
      } else if (type && type.toLowerCase() === "active" && category && category.toLowerCase() === 'zczp') {
        loadIssueInformation();
        if (apiData.demandGraph) {
          loadNseDemandGraphSeries(apiData.demandGraph);
          if (apiData.demandGraph.seriesMap) {
            loadNseGraph(apiData.demandGraph.seriesMap, "series");
          }
          if (apiData.demandGraph.plotData) {
            loadNseGraph(apiData.demandGraph.plotData, "plot");
            loadNseDemandGraphBid(apiData.demandGraph.plotData);
          }
        }
        loadNseDemandGraph(apiData.demandGraph);
        loadDemandData(symbol, series);
        $('#issueInfoTab a[href="#ci_bid_details"]').hide();
        $('#issueInfoTab a[href="#ci_demandDetail"]').hide();
      } else if (type && type.toLowerCase() === "past" && category && category.toLowerCase() === 'zczp') {
        loadIssueInformation();
        $('#issueInfoTab a[href="#ci_bid_details"]').hide();
      } else if (category && category.toLowerCase() === 'lwf') {
        loadIssueInformation();
        $('#issueInfoTab a[href="#ci_bid_details"]').hide();
      } else {
        $('#issueInfoTab a[href="#ci_bid_details"]').tab("show");
        loadIssueInformation();
        loadBidDetails(symbol, series, type);
        if (series.toString().toLowerCase() !== "sme") {
          loadConBidDetails(symbol, series, type);
        }
        if (series.toString().toLowerCase() === "sme") {
          $('.consoldatedbiddetails').addClass("hide");
          $('.all').addClass("hide");
        }
        if (type && type.toLowerCase() !== "past") {
          loadNseDemandGraph(apiData.demandGraph);
        }
        if (type && type.toLowerCase() !== "past" && apiData.demandGraph) {
          loadNseDemandGraphSeries(apiData.demandGraph);
          if (apiData.demandGraph.seriesMap) {
            loadNseGraph(apiData.demandGraph.seriesMap, "series");
          }
        }
        if (type && type.toLowerCase() !== "past" && apiData.demandGraph && apiData.demandGraph.plotData) {
          loadNseGraph(apiData.demandGraph.plotData, "plot");
          loadNseDemandGraphBid(apiData.demandGraph.plotData);
        }
        //loadNseBseDemandGraph();
        //loadNseBseDemandGraphSeries();
        //loadNseBseGraph();

        loadDemandData(symbol, series);
      }
    });
  } catch (e) {
    console.log(e);
  }
};

var loadLwfData = function loadLwfData(symbol, category, issueType) {
  try {
    var uri = void 0;
    if (typeof symbol === "undefined" || symbol === null) {
      alert("Symbol Missing !!! Unable to fetch data");
      return;
    }
    if (typeof symbol !== "undefined" && symbol !== null) {
      uri = "/api/lwf-detail?symbol=" + encodeURIComponent(symbol);
    }
    B.get(uri).then(function (resp) {
      apiData = JSON.parse(resp);
      if (category && category.toLowerCase() === 'lwf') {
        loadIssueInformationLwf();
        $('#issueInfoTab a[href="#ci_bid_details"]').hide();
        $('#issueInfoTab a[href="#ci_nse_demandgraph"]').hide();
        $('#issueInfoTab a[href="#ci_demandDetail"]').hide();
      }
      if (category && category.toLowerCase() === 'lwf' && issueType === 'Active') {
        console.log('inside demand daata');
        $('#issueInfoTab a[href="#ci_lwpdemandDetail"]').show();
        var lwfDemandTable = void 0;
        B.get("/json/liveMarket/lwfDemand.json").then(function (resp) {
          var respJSONObj = JSON.parse(resp);
          if (lwfDemandTable === undefined) {
            lwfDemandTable = customTableNoHead({
              tableStyle: {
                id: "",
                class: ""
              },
              colData: respJSONObj.columns || [],
              rowData: []
            });
            B.render(lwfDemandTable, B.findOne("#table-lwfDemandTable"));
          } else {
            lwfDemandTable.state.rowData = [];
            B.findOne("#table-lwfDemandTable .emptyRow").innerHTML = loader;
          }
          B.get("/api/lwf-demand-data?symbol=" + encodeURIComponent(symbol)).then(function (resp) {
            var respJSON = JSON.parse(resp);
            lwfDemandTable.state.rowData = respJSON.data || [];
            $("#iwfDemandGraphTimestamp").text(respJSON.timeStamp ? 'Updated as on ' + respJSON.timeStamp : '');
          });
          includeJs("/assets/js/deque-patterns.min.js");
        });
      }
    });
  } catch (e) {
    console.log(e);
  }
};

// Add i tag to r[prop] based on a condition srNo
// 1(a)
var convertToItalic = function convertToItalic(r, prop) {
  // return (/[a-z]/i).test(r.srNo || "-") ? '<i>' + r[prop] + '<i>' :   ((r.srNo || "0") % 1 ==0) ? '<b>' + r[prop] + '<b>' : r[prop];
  return (r.srNo || "0") % 1 == 0 ? '<b>' + r[prop] + '<b>' : '<i>' + r[prop] + '</i>';
};
B.on(document, "allGood", function () {
  var symbolName = getParameterByName("symbol");
  var seriesName = getParameterByName("series");
  seriesType = getParameterByName("series");
  var issueType = getParameterByName("type");
  var appType = getParameterByName("rights") === "" ? "rights" : "";
  var category = getParameterByName("cat");
  getCompanyClarificationData(symbolName).then(function (data) {
    // console.log('companyClarificationUrl', data);
    // console.log('further processing');
    companyClarificationURL = '';
    if (data) {
      companyClarificationURL = data;
    }
    if (category === 'lwf') {
      loadLwfData(symbolName, category, issueType);
    } else {
      loadAPIData(symbolName, seriesName, issueType, appType, category);
    }
  }).catch(function (err) {
    // console.log('getCompanyClarificationData', err);
    if (category === 'lwf') {
      loadLwfData(symbolName);
    } else {
      loadAPIData(symbolName, seriesName, issueType, appType, category);
      loadAPIData(symbolName, seriesName, issueType, appType, category);
    }
  });

  if (issueType && issueType.toLowerCase() === "past") {
    $("#issueInfoTab li").eq(2).hide();
    $("#issueInfoTab li").eq(3).hide();
  }
  if (issueType && issueType.toLowerCase() === "active" && appType && appType.toLowerCase() === "rights") {
    $("#info").hide();
  }

  $("#bidDetailsDropdown").change(function (e) {
    $(".bidDetailsTable").hide();
    $("#" + $(this).val()).fadeIn();
  });
  $("#bidDetailsDropdown").val("publicIssuesBidWrapper").change();

  /* Demand Graph */

  $("#demandGraphSelect").change(function (e) {
    var activeValue = $(this).val();
    $("#nseGraph").empty();
    $("#nseDemandGraph").empty();
    $("#nseDemandGraphSeries").empty();
    switch (activeValue) {
      case "NSE":
        console.log("apiData-=in nse-=-", apiData);
        loadNseDemandGraph(apiData.demandGraph);
        if (apiData.demandGraph) {
          loadNseDemandGraphSeries(apiData.demandGraph);

          if (apiData.demandGraph.seriesMap) {
            loadNseGraph(apiData.demandGraph.seriesMap, "series");
          }
        }
        if (apiData.demandGraph && apiData.demandGraph.plotData) {
          loadNseGraph(apiData.demandGraph.plotData, "plot");
          loadNseDemandGraphBid(apiData.demandGraph.plotData);
        }
        // const timestampAll1=apiData.demandGraph.TIMESTAMP == undefined? "Updated " + apiData.demandGraph.timestamp || "" : "Updated " +apiData.demandGraph.TIMESTAMP || ""

        //  $("#demandGraphTimestamp").text(
        //   timestampAll1
        //   );

        if (apiData.demandGraph && apiData.demandGraph.TIMESTAMP != undefined) {
          $("#demandGraphTimestamp").text("Updated " + apiData.demandGraph.TIMESTAMP);
        } else if (apiData.demandGraph && apiData.demandGraph.timestamp != undefined) {
          $("#demandGraphTimestamp").text("Updated " + apiData.demandGraph.timestamp);
        } else {
          $("#demandGraphTimestamp").text("");
        }

        break;
      case "ALL":
        console.log("apiData-=in all-=-", apiData);

        loadNseDemandGraph(apiData.demandGraphALL); // for table
        if (apiData.demandGraphALL) {
          loadNseDemandGraphSeries(apiData.demandGraphALL);
          if (apiData.demandGraphALL.seriesMap) {
            loadNseGraph(apiData.demandGraphALL.seriesMap, "series");
          }
        }
        if (apiData.demandGraphALL && apiData.demandGraphALL.plotData) {
          loadNseGraph(apiData.demandGraphALL.plotData, "plot");
          loadNseDemandGraphBid(apiData.demandGraphALL.plotData);
        }
        // const timestampAll=apiData.demandGraphALL.TIMESTAMP == undefined? "Updated " + apiData.demandGraphALL.timestamp || "": "Updated " + apiData.demandGraphALL.TIMESTAMP || ""
        // console.log("apiData.demandGraphALL.TIMESTAMP--=-",apiData.demandGraphALL.TIMESTAMP)
        //   $("#demandGraphTimestamp").text(
        //     timestampAll
        //   );
        if (apiData.demandGraphALL && apiData.demandGraphALL.TIMESTAMP != undefined) {
          $("#demandGraphTimestamp").text("Updated " + apiData.demandGraphALL.TIMESTAMP);
        } else if (apiData.demandGraphALL && apiData.demandGraphALL.timestamp != undefined) {
          $("#demandGraphTimestamp").text("Updated " + apiData.demandGraphALL.timestamp);
        } else {
          $("#demandGraphTimestamp").text("");
        }

        break;
    }
  });
  /* End */
});

function disclaimerNote() {
  try {
    B.get('/api/disclaimer').then(function (resp) {
      var respJSON = JSON.parse(resp);
      var disclaimerContent = [];

      respJSON && respJSON.content && respJSON.content.field_components && respJSON.content.field_components.map(function (item) {
        disclaimerContent.push(item);
      });

      if (disclaimerContent.length) {
        $('#disclaimerNotes, #disclaimerNotes_consolidated, #disclaimerNotesDD').append("<div class=\"note_container\">\n                          <h3>\n                              <span>" + disclaimerContent[0].field_note_title.trim().replace(/(<p[^>]+?>|<p>|<\/p>)/img, "") + "</span>\n                          </h3>\n                          " + disclaimerContent[1].field_note_para.trim() + "\n                          </div>");
      } else {
        $('#disclaimerNotes, #disclaimerNotes_consolidated, #disclaimerNotesDD').append("<div class=\"note_container\">\n              <h3>\n                  <span>Note</span>\n              </h3>\n              No records found\n              </div>");
      }
    });
  } catch (e) {
    console.log(e);
    $('#disclaimerNotes, #disclaimerNotes_consolidated, #disclaimerNotesDD').append('<div class="note_containerr">No Records</div>');
  }
}

function disclaimerNoteDg() {
  try {
    B.get('/api/disclaimerDg').then(function (resp) {
      var respJSON = JSON.parse(resp);
      var disclaimerContentDg = [];

      respJSON && respJSON.content && respJSON.content.field_components && respJSON.content.field_components.map(function (item) {
        disclaimerContentDg.push(item);
      });

      if (disclaimerContentDg.length) {
        $('#disclaimerNotesDg').append("<div class=\"note_container\">\n                          <h3>\n                              <span>" + disclaimerContentDg[0].field_note_title.trim().replace(/(<p[^>]+?>|<p>|<\/p>)/img, "") + "</span>\n                          </h3>\n                          " + disclaimerContentDg[1].field_note_para.trim() + "\n                          </div>");
      } else {
        $('#disclaimerNotesDg').append("<div class=\"note_container\">\n              <h3>\n                  <span>Note</span>\n              </h3>\n              No records found\n              </div>");
      }
    });
  } catch (e) {
    console.log(e);
    $('#disclaimerNotesDg').append('<div class="p-3 borderBottom text-center">No Records</div>');
  }
}

function getCompanyClarificationData(symbol) {
  try {
    return new Promise(function (resolve, reject) {
      // symbol = 'TATASTEEL';
      // console.log('symbol', symbol);
      B.get('/api/companyClarification').then(function (resp) {
        var respJSON = JSON.parse(resp);
        // console.log('/api/companyClarification', respJSON);
        if (respJSON && respJSON.content && respJSON.content.field_component && respJSON.content.field_component.length > 0) {
          var ipo_symbol_with_url_comp = respJSON.content.field_component[0].ipo_symbol_with_url_comp;
          // console.log('ipo_symbol_with_url_comp', ipo_symbol_with_url_comp);
          if (ipo_symbol_with_url_comp && 'field_ipo_symbol_with_url_comp' in ipo_symbol_with_url_comp && ipo_symbol_with_url_comp.field_ipo_symbol_with_url_comp) {
            var arr = ipo_symbol_with_url_comp.field_ipo_symbol_with_url_comp;
            var filteredSymbol = arr.filter(function (item) {
              return item.ipo_symbol_with_url.field_symbol === symbol;
            });
            if (filteredSymbol && filteredSymbol.length > 0) {
              // console.log('filteredSymbol', filteredSymbol);
              if (filteredSymbol[0].ipo_symbol_with_url && filteredSymbol[0].ipo_symbol_with_url.field_url && filteredSymbol[0].ipo_symbol_with_url.field_url.url) {
                resolve(filteredSymbol[0].ipo_symbol_with_url.field_url.url);
              }
            }
          }
        }
        resolve(null);
      });
    });
  } catch (e) {
    console.log(e);
  }
}