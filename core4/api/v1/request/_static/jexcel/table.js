class DataTable {
    constructor(option) {
        this.option = option;
        this.option.page_count = null;
        this.option.total_count = 0;
        this.option.count = null;
        this.column = new Set();
        this.option.sort_order = null;
        this.table = jexcel(document.getElementById(this.option._id), {
            tableWidth: this.option.width,
            tableHeight: this.option.height,
            tableOverflow: true,
            columnDrag: true,
            rowDrag: false,
            editable: false,
            onsort: this.sort.bind(this),
            onmovecolumn: this.move.bind(this),
        });
        //console.log(this.option);
    }
    move(instance, from, to) {
        var s  = Array.from(this.column);
        var temp = s[from];
        s[from] = s[to];
        s[to] = temp;
        this.column = new Set(s);
        this.redraw();
    }
    sort(instance, cellNum, order) {
        this.option.current_page = 0;
        var order = (order) ? -1 : 1;
        var colName = Array.from(this.column)[cellNum];
        this.option.sort_order = {
            column: colName,
            by: order
        }
        this.query();
        return false;
    }
    run() {
        this.query();
    }
    next_page() {
        this.option.current_page += 1;
        this.query();
    }
    previous_page() {
        this.option.current_page -= 1;
        this.query();
    }
    redraw() {
        var canvas = document.createElement("canvas");
        var ctx = canvas.getContext("2d");
        var fontfamily = $("#" + this.option._id + " td").css("font-family");
        var fontsize = $("#" + this.option._id + " td").css("font-size");
        ctx.font = fontsize + " " + fontfamily;
        for (var i=0; i<this.column.size; i++) {
            this.table.setHeader(i, Array.from(this.column)[i]);
            var mx = ctx.measureText(this.table.getHeader(i)).width;
            var txt = this.table.getColumnData(i);
            txt.forEach(function(v) {
                var w = ctx.measureText(v);
                if (w.width > mx) {
                    mx = w.width;
                }
            });
            // console.log(mx);
            this.table.setWidth(i, mx + 24);
        }
        this.table.resetSelection();
    }
    query() {
        if (this.option.current_page >= this.option.page_count) {
            this.option.current_page = 0;
        }
        var url = this.option.url + '?page=' + this.option.current_page;
        if (this.option.sort_order != null) {
            url += '&sort=[["' + this.option.sort_order.column + '",';
            url += this.option.sort_order.by + "]]";
        }
        url += this.get_input("filter");
        url += this.get_input("column");
        url += this.get_input("per_page");
        // console.log(url);

        console.log(this.option.column);
        var table = this.table;
        $.ajax({
            url: url,
            type: this.option.method,
            success: function(data) {
                table.options.allowInsertRow = true;
                table.options.allowInsertColumn = true;
                table.options.allowManualInsertColumn = true;
                table.options.allowDeleteRow = true;
                table.options.allowDeleteColumn = true;
                table.options.allowRenameColumn = true;
                table.setData([[]]);
                var table_data = new Array();

                this.option.current_page = data.page;
                this.option.total_count = data.total_count;
                this.option.page_count = data.page_count;
                this.option.per_page = data.per_page;
                this.option.count = data.count;
                for (var rec in data.data) {
                    var row = new Array();
                    for (var fld in data.data[rec]) {
                        this.column.add(fld);
                        var pos = Array.from(this.column).indexOf(fld);
                        row[pos] = data.data[rec][fld];
                    }
                    table_data.push(row);
                    //console.log(row);
                }
                // var column_width = 1000 / (this.column.size + 1);
                if (table.getHeaders().length == 0) {
                    this.column.forEach(function(v) {
                        table.insertColumn([], 0, 0, {readonly: true});
                    })
                }
                table.setData(table_data);

                this.redraw();

                var s = this.table.getColumnData(0).length;
                //console.log(s);
                //console.log(this.option.count);
                if (s > this.option.count) {
                    //console.log("GO DEL");
                    this.table.deleteRow(s, this.option.count);
                }

                table.options.allowInsertRow = false;
                table.options.allowInsertColumn = false;
                table.options.allowManualInsertColumn = false;
                table.options.allowDeleteRow = false;
                table.options.allowDeleteColumn = false;
                table.options.allowRenameColumn = false;
                //table.deleteRow(9, 100);
                //console.log(table)
                this.set_input("page", this.option.current_page + 1);
                this.set_input("page_count", this.option.page_count);
                this.set_input("total_count", this.option.total_count);
                this.set_input("per_page", this.option.per_page);
                this.set_input("filter", JSON.stringify(this.option.filter));
                this.set_input("column", JSON.stringify(this.option.column));

            }.bind(this)
        });
    }
    set_input(key, value) {
        var elem = $("." + this.option._id + "-" + key);
        elem.each(function() {
            if (this.tagName == "INPUT") {
                elem.val(value);
            }
            else {
                elem.text(value);
            }
        });
    }
    get_input(key) {
        var elem = $("#" + this.option._id + "-" + key);
        if ((elem.val() != null) & (elem.val() != "")) {
            return "&" + key + "=" + elem.val();
        }
        else {
            return ""
        }
    }

}
