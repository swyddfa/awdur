import { Application } from "./app";
import { IndexedDBScriptAccess } from "./services/indexeddb";

let access = new IndexedDBScriptAccess()
let application = new Application(access);
application.main()