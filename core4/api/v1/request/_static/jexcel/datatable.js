class DataTable {
    constructor(option) {
        // option:
        //   _id, url, method, current_page, per_page, filter, width, height
        this.option = option;
        this.page_count = null;
        this.total_count = 0;
        this.count = null;
        this.sort_order = null;
        this.table = jexcel(document.getElementById(this.option._id), {
            tableWidth: this.option.width,
            tableHeight: this.option.height,
            tableOverflow: true,
            columnDrag: true,
            rowDrag: false,
            editable: false,
        });
        this.orderStack = new Array();
        this.table.orderBy = this.orderBy.bind(this);
        this.set_current_page(this.option.current_page);
        this.set_per_page(this.option.per_page);
        this.set_column(JSON.stringify(this.option.column));
        this.set_filter(JSON.stringify(this.option.filter));
        this.log("init with " + JSON.stringify(this.option));
    }
    log(s){
        console.log(s);
    }
    orderBy(column, order) {
        if (order == null) {
            order = this.table.headers[column].classList.contains('arrow-down') ? 1 : 0;
        } else {
            order = order ? 1 : 0;
        }
        var pos = this.orderStack.map(function(e) {
            return e.num;
        }).indexOf(column);
        if (pos >= 0) {
            this.orderStack = this.orderStack.slice(0, pos);
        }
        this.orderStack = [{"num": column, "by": order}].concat(
            this.orderStack);
        this.table.updateOrderArrow(column, order);
        this.set_current_page(0);
        this.update();
    }
    set_current_page(p) {
        $("." + this.get_name("current_page")).text(p);
        $("#" + this.get_name("current_page")).val(p);
        this.option.current_page = p;
    }
    get_current_page() {
        return parseInt($("#" + this.get_name("current_page")).val());
    }
    set_per_page(pp) {
        $("#" + this.get_name("per_page")).val(pp);
        this.option.per_page = pp;
    }
    get_per_page() {
        return parseInt($("#" + this.get_name("per_page")).val());
    }
    set_filter(f) {
        $("." + this.get_name("filter")).text(f);
        $("#" + this.get_name("filter")).val(f);
    }
    get_filter() {
        var f = $("#" + this.get_name("filter")).val();
        if (f == "") {
            this.set_filter("{}");
            return "{}";
        }
        return f;
    }
    set_column(c) {
        $("." + this.get_name("column")).text(c);
        $("#" + this.get_name("column")).val(c);
    }
    get_column() {
        var f = $("#" + this.get_name("column")).val();
        if (f == "") {
            return "[]";
        }
        return f;
    }
    set_page_count(p) {
        $("." + this.get_name("page_count")).text(p);
    }
    set_total_count(p) {
        $("." + this.get_name("total_count")).text(p);
    }
    update() {
        var url = this.build_url();
        this.log(this.option.method + ": " + url);
        $.ajax({
            url: url,
            type: this.option.method,
            success: function(data) {
                this.page_count = data.page_count;
                this.total_count = data.total_count;
                this.count = data.count;
                this.log("success with " + this.count + " records, "
                         + this.page_count + " pages, "
                         + this.total_count + " total records");
                this.set_per_page(data.per_page);
                this.set_page_count(data.page_count);
                this.set_total_count(data.total_count);
                if (data.page >= this.page_count) {
                    this.set_current_page(0);
                    if (this.page_count > 0) {
                        this.update();
                    }
                }
                else {
                    this.set_current_page(data.page);
                    this.load_data(data.data);
                }
            }.bind(this)
        });
    }
    lookup() {
        var lookup = new Array();
        var cols = JSON.parse(this.get_column());
        for (var i=0; i<cols.length; i++) {
            var col = cols[i];
            if (col.visible) {
                lookup.push({
                    "name": col.name,
                    "title": col.title,
                    "align": col.align
                })
            }
        }
        return lookup;
    }
    load_data(data) {
        var lookup = this.lookup();
        while (this.table.headers.length > 1) {
            this.table.deleteColumn(0);
        }
        var insert = new Array();
        for (var row in data) {
            var rec = new Array();
            for (var fld in data[row]) {
                var pos = lookup.map(function(e) { return e.name; }).indexOf(fld);
                rec[pos] = data[row][fld];
            }
            insert.push(rec);
        }
        while (this.table.headers.length < lookup.length) {
            this.table.insertColumn([], 0, 0);
        }
        for (var col in lookup) {
            this.table.setHeader(col, lookup[col].title);
        }
        this.table.setData(insert);
        this.redraw(lookup);
    }
    redraw(lookup) {
        var canvas = document.createElement("canvas");
        var ctx = canvas.getContext("2d");
        var fontfamily = $("#" + this.option._id + " td").css("font-family");
        var fontsize = $("#" + this.option._id + " td").css("font-size");
        ctx.font = fontsize + " " + fontfamily;
        for (var i=0; i<lookup.length; i++) {
            var mx = ctx.measureText(this.table.getHeader(i)).width;
            var txt = this.table.getColumnData(i);
            var elem = $("#" + this.option._id + " tbody [data-x='" + i + "']");
            elem.each(function(){
                this.style["text-align"] = lookup[i].align;
            });
            txt.forEach(function(v) {
                var w = ctx.measureText(v);
                if (w.width > mx) {
                    mx = w.width;
                }
            });
            this.table.setWidth(i, mx + 24);
        }
        this.table.resetSelection();
        if (this.orderStack.length > 0){
            var col = this.orderStack[0]["num"];
            var by = this.orderStack[0]["by"];
            this.table.updateOrderArrow(col, by);
        }
    }
    build_url() {
        var url = this.option.url;
        url += '?page=' + this.get_current_page();
        url += "&per_page=" + this.get_per_page();
        url += "&filter=" + this.get_filter();
        if (this.orderStack.length > 0){
            var lookup = this.lookup();
            var sort = new Array();
            for (var i=0; i<this.orderStack.length; i++) {
                var col = lookup[this.orderStack[i]["num"]];
                var by = this.orderStack[i]["by"] ? 1 : -1;
                sort.push([col["name"], by]);
            }
            url += "&sort=" + JSON.stringify(sort);
        }
        //url += "&column=" + this.get_column();
        return url;
    }
    next_page() {
        this.set_current_page(this.get_current_page() + 1);
        this.update();
    }
    previous_page() {
        this.set_current_page(this.get_current_page() - 1);
        this.update();
    }
    get_name(key) {
        return this.option._id + "-" + key;
    }
}