import { Application } from "./app";

class WebApplication extends Application {

}

let appRoot = document.querySelector('main')
let application = new WebApplication(appRoot);
application.main()