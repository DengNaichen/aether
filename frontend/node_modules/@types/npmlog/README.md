# Installation
> `npm install --save @types/npmlog`

# Summary
This package contains type definitions for npmlog (https://github.com/npm/npmlog#readme).

# Details
Files were exported from https://github.com/DefinitelyTyped/DefinitelyTyped/tree/master/types/npmlog.
## [index.d.ts](https://github.com/DefinitelyTyped/DefinitelyTyped/tree/master/types/npmlog/index.d.ts)
````ts
/// <reference types="node" />

import { EventEmitter } from "events";

declare namespace npmlog {
    // TODO: newStream, newGroup, setGaugeTemplate and setGaugeTemplateSet need to be added
    interface Logger extends EventEmitter {
        (): any;

        level: string;
        record: MessageObject[];
        maxRecordSize: number;
        prefixStyle: StyleObject;
        headingStyle: StyleObject;
        heading: string;
        stream: any; // Defaults to process.stderr

        log(level: LogLevels | string, prefix: string, message: string, ...args: any[]): void;

        silly(prefix: string, message: string, ...args: any[]): void;
        verbose(prefix: string, message: string, ...args: any[]): void;
        info(prefix: string, message: string, ...args: any[]): void;
        timing(prefix: string, message: string, ...args: any[]): void;
        http(prefix: string, message: string, ...args: any[]): void;
        notice(prefix: string, message: string, ...args: any[]): void;
        warn(prefix: string, message: string, ...args: any[]): void;
        error(prefix: string, message: string, ...args: any[]): void;
        silent(prefix: string, message: string, ...args: any[]): void;

        enableColor(): void;
        disableColor(): void;

        enableProgress(): void;
        disableProgress(): void;
        progressEnabled(): boolean;

        enableUnicode(): void;
        disableUnicode(): void;

        pause(): void;
        resume(): void;

        addLevel(level: string, n: number, style?: StyleObject, disp?: string): void;

        // Allows for custom log levels
        // npmlog.addLevel("custom", level)
        // npmlog.custom(prefix, message)
        [key: string]: any;
    }

    type LogLevels = "silly" | "verbose" | "info" | "timing" | "http" | "notice" | "warn" | "error" | "silent";

    interface StyleObject {
        fg?: string | undefined;
        bg?: string | undefined;
        bold?: boolean | undefined;
        inverse?: boolean | undefined;
        underline?: boolean | undefined;
        bell?: boolean | undefined;
    }

    interface MessageObject {
        id: number;
        level: string;
        prefix: string;
        message: string;
        messageRaw: string;
    }
}

declare var npmlog: npmlog.Logger;
export = npmlog;

````

### Additional Details
 * Last updated: Tue, 07 Nov 2023 09:09:39 GMT
 * Dependencies: [@types/node](https://npmjs.com/package/@types/node)

# Credits
These definitions were written by [Daniel Schmidt](https://github.com/DanielMSchmidt), and [Joseph Wynn](https://github.com/wildlyinaccurate).
