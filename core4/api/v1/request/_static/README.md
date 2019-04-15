# CORE4OS Widgets

In CORE4OS there are widgets and boards. 

Widgets are small or even very large programs. These service or auxiliary programs can be, for example, a link list to access your BI applications, a summary of your company's main performance indicators and a gateway to access your raw data. They facilitate access to complex or simple functions. 

Widgets can have different states. A normal view and a maximum view that opens in fullscreen when you click on the widget. The normal view often offers only a reduced number of functions or it is just a link to the maximum view of the widget. 

Boards contain any number of widgets and facilitate access to widgets. They can be compiled or deleted and can contain thematically related widgets.

## Getting Started

Widgets included some standard dependencies:
* bootstrap-material-design.custom.css (Customized version of  [BS Material Design](https://fezvrasta.github.io/bootstrap-material-design/docs/4.0/getting-started/introduction/))
* Jquery  [Jquery Slim](https://jquery.com/)
* Popper  [Popper.js](https://popper.js.org/)
* bootstrap-material-design  [BS Material Design](https://fezvrasta.github.io/bootstrap-material-design/docs/4.0/getting-started/introduction/)

All JavaScript files have been packaged into one file:

**jq.pop.bsmd.min.js**

### Default widget template for developers

```
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>title</title>
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <link rel="stylesheet" type="text/css" href="{{ default_static('widget/bootstrap-material-design.custom.css') }}">
</head>
<div class="container">
    content
</div>
<script src="{{ default_static('widget/jq.pop.bsmd.min.js') }}"></script>
</body>
</html>
```

### Botrap Material Design Documentation

[BS Material Design Documentation](https://fezvrasta.github.io/bootstrap-material-design/docs/4.0/getting-started/introduction/)

