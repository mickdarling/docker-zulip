/*
    content_action_registry

    Extensible registry for content-aware action icons in rendered messages.
    Actions are matched against file links (by extension, URL pattern, or
    content pattern) and rendered as inline buttons next to matching elements.

    Register new actions with registerContentAction(). The rendering engine
    in rendered_markdown.ts processes them generically.
*/

export interface ContentAction {
    id: string;
    label: string;
    icon: string;
    match: {
        type: "file_extension" | "url_pattern" | "content_pattern";
        value: string | string[] | RegExp;
    };
    handler: (context: ActionContext) => void | Promise<void>;
    style?: {
        hue: number;
    };
}

export interface ActionContext {
    element: HTMLAnchorElement;
    href: string;
    filePath?: string;
    fileName?: string;
}

const registry: ContentAction[] = [];

export function registerContentAction(action: ContentAction): void {
    // Prevent duplicate registrations
    if (registry.some((a) => a.id === action.id)) {
        return;
    }
    registry.push(action);
}

export function getMatchingActions(context: {
    href: string;
    fileName: string;
}): ContentAction[] {
    return registry.filter((action) => matchesAction(action, context));
}

function matchesAction(
    action: ContentAction,
    context: {href: string; fileName: string},
): boolean {
    const {type, value} = action.match;

    switch (type) {
        case "file_extension": {
            const extensions = Array.isArray(value) ? value : [value];
            const lowerName = context.fileName.toLowerCase();
            return extensions.some(
                (ext) => typeof ext === "string" && lowerName.endsWith(ext.toLowerCase()),
            );
        }
        case "url_pattern": {
            if (value instanceof RegExp) {
                return value.test(context.href);
            }
            const patterns = Array.isArray(value) ? value : [value];
            return patterns.some(
                (pattern) => typeof pattern === "string" && context.href.includes(pattern),
            );
        }
        case "content_pattern": {
            if (value instanceof RegExp) {
                return value.test(context.href);
            }
            return false;
        }
        default:
            return false;
    }
}

// === Built-in actions ===

// Merview: Open .md file attachments in the Merview renderer
const MERVIEW_BASE_URL = "https://merview.com/";

registerContentAction({
    id: "merview",
    label: "Merview",
    icon: "zulip-icon-external-link",
    match: {type: "file_extension", value: [".md", ".markdown", ".mdx"]},
    handler: async (ctx) => {
        const pathMatch = ctx.href.match(/\/user_uploads\/(.+)/);
        if (!pathMatch) {
            console.error("[ContentAction:merview] Could not extract file path from href:", ctx.href);
            return;
        }

        try {
            const response = await fetch(`/json/user_uploads/${pathMatch[1]}`);
            const data = (await response.json()) as {result: string; url?: string};

            if (data.result === "success" && data.url) {
                const fullTempUrl = new URL(data.url, window.location.origin).href;
                const merviewUrl = `${MERVIEW_BASE_URL}?url=${fullTempUrl}`;
                window.open(merviewUrl, "_blank", "noopener,noreferrer");
            } else {
                console.error("[ContentAction:merview] Failed to get temporary URL:", data);
            }
        } catch (error) {
            console.error("[ContentAction:merview] Error fetching temporary URL:", error);
        }
    },
    style: {hue: 200},
});
