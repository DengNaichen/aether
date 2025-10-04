import { RunnerTask } from 'vitest';
import { Channel } from 'storybook/internal/channels';

declare global {
    var __STORYBOOK_ADDONS_CHANNEL__: Channel;
}
type Task = Partial<RunnerTask> & {
    meta: Record<string, any>;
};
declare const modifyErrorMessage: ({ task }: {
    task: Task;
}) => void;

export { Task, modifyErrorMessage };
