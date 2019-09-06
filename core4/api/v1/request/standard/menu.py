from core4.api.v1.request.main import CoreRequestHandler
class AboutHandler(CoreRequestHandler):
    author = "mmr"
    title = "About Core4"
    icon = "more"
    tag = ["Example", "cre4ui", "Menu"]

    async def get(self):
        self.render("template/about.html")
