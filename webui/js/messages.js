// copy button
import { openImageModal } from "./image_modal.js";

function createCopyButton() {
  const button = document.createElement("button");
  button.className = "copy-button";
  button.textContent = "Copy";

  button.addEventListener("click", async function (e) {
    e.stopPropagation();
    const container = this.closest(".msg-content, .kvps-row, .message-text");
    let textToCopy;

    if (container.classList.contains("kvps-row")) {
      textToCopy = container.querySelector(".kvps-val").textContent;
    } else if (container.classList.contains("message-text")) {
      textToCopy = container.querySelector("span").textContent;
    } else {
      textToCopy = container.querySelector("span").textContent;
    }

    try {
      await navigator.clipboard.writeText(textToCopy);
      const originalText = button.textContent;
      button.classList.add("copied");
      button.textContent = "Copied!";
      setTimeout(() => {
        button.classList.remove("copied");
        button.textContent = originalText;
      }, 2000);
    } catch (err) {
      console.error("Failed to copy text:", err);
    }
  });

  return button;
}

function addCopyButtonToElement(element) {
  if (!element.querySelector(".copy-button")) {
    element.appendChild(createCopyButton());
  }
}

export function getHandler(type) {
  switch (type) {
    case "user":
      return drawMessageUser;
    case "agent":
      return drawMessageAgent;
    case "response":
      return drawMessageResponse;
    case "tool":
      return drawMessageTool;
    case "code_exe":
      return drawMessageCodeExe;
    case "browser":
      return drawMessageBrowser;
    case "warning":
      return drawMessageWarning;
    case "rate_limit":
      return drawMessageWarning;
    case "error":
      return drawMessageError;
    case "info":
      return drawMessageInfo;
    case "util":
      return drawMessageUtil;
    case "hint":
      return drawMessageInfo;
    default:
      return drawMessageDefault;
  }
}

// draw a message with a specific type
export function _drawMessage(
  messageContainer,
  heading,
  content,
  temp,
  followUp,
  kvps = null,
  messageClasses = [],
  contentClasses = [],
  latex = false
) {
  let messageDiv = messageContainer.querySelector('.message');
  let headingElement = messageDiv ? messageDiv.querySelector('h4') : null;
  let preElement = messageDiv ? messageDiv.querySelector('pre.msg-content') : null;
  let spanElement = preElement ? preElement.querySelector('span') : null;
  let kvpsDl = messageDiv ? messageDiv.querySelector('dl.message-details') : null;

  // If the inner messageDiv doesn't exist, create the full structure.
  if (!messageDiv) {
    messageContainer.innerHTML = ''; // Clear potential old content if messageContainer was reused for a new message type
    messageDiv = document.createElement("div");
    messageDiv.classList.add("message", ...messageClasses);
    messageContainer.appendChild(messageDiv);

    headingElement = document.createElement("h4");
    messageDiv.appendChild(headingElement);

    // Create KVPs container if needed
    if (kvps) {
        kvpsDl = document.createElement("dl");
        kvpsDl.classList.add("message-details");
        messageDiv.appendChild(kvpsDl);
    }

    preElement = document.createElement("pre");
    preElement.classList.add("msg-content", ...contentClasses);
    preElement.style.whiteSpace = "pre-wrap";
    preElement.style.wordBreak = "break-word";

    spanElement = document.createElement("span");
    preElement.appendChild(spanElement);
    addCopyButtonToElement(preElement);
    messageDiv.appendChild(preElement);

    // Add click handler for small screens only on creation
    spanElement.addEventListener("click", () => {
      copyText(spanElement.textContent, spanElement);
    });
  } else {
      // Ensure messageDiv has correct classes, especially if type changed
      messageDiv.classList.remove(...messageDiv.classList);
      messageDiv.classList.add("message", ...messageClasses);

      // If KVPs are updated or appear, and no existing KVPs DL, redraw.
      // This might be imperfect if KVPs *change* rather than just appear/append.
      if (kvps && !kvpsDl) {
          kvpsDl = document.createElement("dl");
          kvpsDl.classList.add("message-details");
          // Insert before preElement if it exists, otherwise append
          if (preElement) {
              messageDiv.insertBefore(kvpsDl, preElement);
          } else {
              messageDiv.appendChild(kvpsDl);
          }
      }
  }

  // Update heading content
  if (headingElement) {
    if (heading === "Agent 0: Generating") {
        headingElement.textContent = "Initiating Directive Protocol";
    } else if (heading === "Agent 0: Responding") {
        headingElement.textContent = "AISIS: Transmitting Acknowledgment";
    } else {
        headingElement.textContent = heading;
    }
  }

  // Update main content
  if (spanElement) {
    spanElement.innerHTML = convertHTML(content);
  }

  // Redraw KVPs if kvpsDl exists (either just created or already existed)
  // This will clear and redraw KVPs on every update, which is acceptable if they change frequently.
  if (kvps && kvpsDl) {
      kvpsDl.innerHTML = ''; // Clear existing KVP items
      drawKvpsContent(kvpsDl, kvps, latex); // Draw new KVP items into the dl
  }

  // Render LaTeX math within the span
  if (window.renderMathInElement && latex && spanElement) {
    renderMathInElement(spanElement, {
      delimiters: [{ left: "$", right: "$", display: true }],
      throwOnError: false,
    });
  }

  // Auto-scroll the *internal* message content to the bottom on update
  // This applies to AI/Tool/Browser messages where content streams.
  const shouldAutoScrollInternal = (
    messageClasses.includes('message-ai') ||
    messageClasses.includes('message-tool') ||
    messageClasses.includes('message-browser')
  );

  if (shouldAutoScrollInternal && preElement) {
    requestAnimationFrame(() => {
      preElement.scrollTop = preElement.scrollHeight;
    });
  }

  if (followUp) {
    messageContainer.classList.add("message-followup");
  } else {
    messageContainer.classList.remove("message-followup");
  }

  return messageDiv;
}

// Extracted KVP drawing logic for reusability and to avoid full element recreation
function drawKvpsContent(dlElement, kvps, latex) {
    for (let [key, value] of Object.entries(kvps)) {
      const divItem = document.createElement("div");
      divItem.classList.add("detail-item");
      if (key === "thoughts" || key === "reflection")
        divItem.classList.add("msg-thoughts");

      const dt = document.createElement("dt");
      dt.textContent = convertToTitleCase(key);
      dt.classList.add("detail-key");
      divItem.appendChild(dt);

      const dd = document.createElement("dd");
      dd.classList.add("detail-value");

      if (Array.isArray(value)) {
        for (const item of value) {
          addValue(item);
        }
      } else {
        addValue(value);
      }

      function addValue(value) {
        if (typeof value === "object") value = JSON.stringify(value, null, 2);

        if (typeof value === "string" && value.startsWith("img://")) {
          const imgElement = document.createElement("img");
          imgElement.classList.add("kvps-img");
          imgElement.classList.add("responsive-screenshot-img");
          imgElement.src = value.replace("img://", "/image_get?path=");
          imgElement.alt = "Image Attachment";
          dd.appendChild(imgElement);

          imgElement.style.cursor = "pointer";
          imgElement.addEventListener("click", () => {
            openImageModal(imgElement.src, 1000);
          });
        } else {
          const pre = document.createElement("pre");
          pre.classList.add("detail-content");

          const span = document.createElement("span");
          span.innerHTML = convertHTML(value);
          pre.appendChild(span);
          dd.appendChild(pre);
          addCopyButtonToElement(dd);

          span.addEventListener("click", () => {
            copyText(span.textContent, span);
          });

          if (window.renderMathInElement && latex) {
            renderMathInElement(span, {
              delimiters: [{ left: "$", right: "$", display: true }],
              throwOnError: false,
            });
          }
        }
      }
      divItem.appendChild(dd);
      dlElement.appendChild(divItem);
    }
}


export function drawMessageDefault(
  messageContainer,
  id,
  type,
  heading,
  content,
  temp,
  kvps = null
) {
  _drawMessage(
    messageContainer,
    heading,
    content,
    temp,
    false,
    kvps,
    ["message-ai", "message-default"],
    ["msg-json"],
    false
  );
}

export function drawMessageAgent(
  messageContainer,
  id,
  type,
  heading,
  content,
  temp,
  kvps = null
) {
  let kvpsFlat = null;
  if (kvps) {
    kvpsFlat = { ...kvps, ...(kvps["tool_args"] || {}) };
    delete kvpsFlat["tool_args"];
  }

  _drawMessage(
    messageContainer,
    heading,
    content,
    temp,
    false,
    kvpsFlat,
    ["message-ai", "message-agent"],
    ["msg-json"],
    false
  );
}

export function drawMessageResponse(
  messageContainer,
  id,
  type,
  heading,
  content,
  temp,
  kvps = null
) {
  _drawMessage(
    messageContainer,
    heading,
    content,
    temp,
    true,
    null,
    ["message-ai", "message-agent-response"],
    [],
    true
  );
}

export function drawMessageDelegation(
  messageContainer,
  id,
  type,
  heading,
  content,
  temp,
  kvps = null
) {
  _drawMessage(
    messageContainer,
    heading,
    content,
    temp,
    true,
    kvps,
    ["message-ai", "message-agent", "message-agent-delegation"],
    [],
    true
  );
}

export function drawMessageUser(
  messageContainer,
  id,
  type,
  heading,
  content,
  temp,
  kvps = null,
  latex = false
) {
  let messageDiv = messageContainer.querySelector('.message-user');
  let headingElement = messageDiv ? messageDiv.querySelector('h4') : null;
  let textDiv = messageDiv ? messageDiv.querySelector('.message-text') : null;
  let spanElement = textDiv ? textDiv.querySelector('span') : null;
  let attachmentsContainer = messageDiv ? messageDiv.querySelector('.attachments-container') : null;

  if (!messageDiv) {
    messageContainer.innerHTML = '';
    messageDiv = document.createElement("div");
    messageDiv.classList.add("message", "message-user");
    messageContainer.appendChild(messageDiv);

    headingElement = document.createElement("h4");
    headingElement.textContent = "User message";
    messageDiv.appendChild(headingElement);

    textDiv = document.createElement("div");
    textDiv.classList.add("message-text");
    spanElement = document.createElement("span");
    textDiv.appendChild(spanElement);

    textDiv.addEventListener("click", () => {
      copyText(content, textDiv);
    });
    addCopyButtonToElement(textDiv);
    messageDiv.appendChild(textDiv);

    attachmentsContainer = document.createElement("div");
    attachmentsContainer.classList.add("attachments-container");
    messageDiv.appendChild(attachmentsContainer);
  }

  // Update content
  if (spanElement && content) {
    spanElement.innerHTML = convertHTML(content);
  }

  // Handle attachments: always re-render the attachments section if kvps.attachments exist
  if (kvps && kvps.attachments && kvps.attachments.length > 0) {
    if (!attachmentsContainer) {
        // This case should ideally not be hit if !messageDiv block creates it
        attachmentsContainer = document.createElement("div");
        attachmentsContainer.classList.add("attachments-container");
        messageDiv.appendChild(attachmentsContainer);
    }
    attachmentsContainer.innerHTML = ''; // Clear existing attachments to re-render
    renderAttachments(attachmentsContainer, kvps.attachments);
  } else if (attachmentsContainer) {
      attachmentsContainer.innerHTML = ''; // Clear attachments if none are provided anymore
  }
}

// Helper function to render attachments (extracted for reusability)
function renderAttachments(container, attachments) {
    attachments.forEach((attachment) => {
        const attachmentDiv = document.createElement("div");
        attachmentDiv.classList.add("attachment-item");

        if (typeof attachment === "string") {
            const filename = attachment;
            const extension = filename.split(".").pop().toUpperCase();

            attachmentDiv.classList.add("file-type");
            attachmentDiv.innerHTML = `
                <div class="file-preview">
                    <span class="filename">${filename}</span>
                    <span class="extension">${extension}</span>
                </div>
            `;
        } else if (attachment.type === "image") {
            const imgWrapper = document.createElement("div");
            imgWrapper.classList.add("image-wrapper");

            const img = document.createElement("img");
            img.src = attachment.url;
            img.alt = attachment.name;
            img.classList.add("attachment-preview");
            img.classList.add("responsive-screenshot-img");

            const fileInfo = document.createElement("div");
            fileInfo.classList.add("file-info");
            fileInfo.innerHTML = `
                <span class="filename">${attachment.name}</span>
                <span class="extension">${attachment.extension.toUpperCase()}</span>
            `;

            imgWrapper.appendChild(img);
            attachmentDiv.appendChild(imgWrapper);
            attachmentDiv.appendChild(fileInfo);
        } else {
            attachmentDiv.classList.add("file-type");
            attachmentDiv.innerHTML = `
                <div class="file-preview">
                    <span class="filename">${attachment.name}</span>
                    <span class="extension">${attachment.extension.toUpperCase()}</span>
                </div>
            `;
        }
        container.appendChild(attachmentDiv);
    });
}

export function drawMessageTool(
  messageContainer,
  id,
  type,
  heading,
  content,
  temp,
  kvps = null
) {
  _drawMessage(
    messageContainer,
    heading,
    content,
    temp,
    true,
    kvps,
    ["message-ai", "message-tool"],
    ["msg-output"],
    false
  );
}

export function drawMessageCodeExe(
  messageContainer,
  id,
  type,
  heading,
  content,
  temp,
  kvps = null
) {
  _drawMessage(
    messageContainer,
    heading,
    content,
    temp,
    true,
    null,
    ["message-ai", "message-code-exe"],
    [],
    false
  );
}

export function drawMessageBrowser(
  messageContainer,
  id,
  type,
  heading,
  content,
  temp,
  kvps = null
) {
  _drawMessage(
    messageContainer,
    heading,
    content,
    temp,
    true,
    kvps,
    ["message-ai", "message-browser"],
    ["msg-json"],
    false
  );
}

export function drawMessageAgentPlain(
  classes,
  messageContainer,
  id,
  type,
  heading,
  content,
  temp,
  kvps = null
) {
  _drawMessage(
    messageContainer,
    heading,
    content,
    temp,
    false,
    kvps,
    [...classes],
    [],
    false
  );
  messageContainer.classList.add("center-container");
}

export function drawMessageInfo(
  messageContainer,
  id,
  type,
  heading,
  content,
  temp,
  kvps = null
) {
  return drawMessageAgentPlain(
    ["message-info"],
    messageContainer,
    id,
    type,
    heading,
    content,
    temp,
    kvps
  );
}

export function drawMessageUtil(
  messageContainer,
  id,
  type,
  heading,
  content,
  temp,
  kvps = null
) {
  _drawMessage(
    messageContainer,
    heading,
    content,
    temp,
    false,
    kvps,
    ["message-util"],
    ["msg-json"],
    false
  );
  messageContainer.classList.add("center-container");
}

export function drawMessageWarning(
  messageContainer,
  id,
  type,
  heading,
  content,
  temp,
  kvps = null
) {
  return drawMessageAgentPlain(
    ["message-warning"],
    messageContainer,
    id,
    type,
    heading,
    content,
    temp,
    kvps
  );
}

export function drawMessageError(
  messageContainer,
  id,
  type,
  heading,
  content,
  temp,
  kvps = null
) {
  return drawMessageAgentPlain(
    ["message-error"],
    messageContainer,
    id,
    type,
    heading,
    content,
    temp,
    kvps
  );
}

function drawKvps(container, kvps, latex) {
  // This function is now simplified, it expects to be called when kvpsDl is newly created or cleared.
  // The actual element is passed in drawKvpsContent.
}

function convertToTitleCase(str) {
  return str
    .replace(/_/g, " ") // Replace underscores with spaces
    .toLowerCase() // Convert the entire string to lowercase
    .replace(/\b\w/g, function (match) {
      return match.toUpperCase(); // Capitalize the first letter of each word
    });
}

function convertImageTags(content) {
  // Regular expression to match <image> tags and extract base64 content
  const imageTagRegex = /<image>(.*?)<\/image>/g;

  // Replace <image> tags with <img> tags with base64 source
  const updatedContent = content.replace(
    imageTagRegex,
    (match, base64Content) => {
      return `<img src="data:image/jpeg;base64,${base64Content}" alt="Image Attachment" class="responsive-screenshot-img"/>`; // Removed inline style
    }
  );

  return updatedContent;
}

async function copyText(text, element) {
  try {
    await navigator.clipboard.writeText(text);
    element.classList.add("copied");
    setTimeout(() => {
      element.classList.remove("copied");
    }, 2000);
  } catch (err) {
    console.error("Failed to copy text:", err);
  }
}

function convertHTML(str) {
  if (typeof str !== "string") str = JSON.stringify(str, null, 2);

  let result = escapeHTML(str);
  result = convertPathsToLinks(result);
  result = convertImageTags(result);
  return result;
}

function escapeHTML(str) {
  const escapeChars = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "'": "&#39;",
    '"': "&quot;",
  };
  return str.replace(/[&<>'"]/g, (char) => escapeChars[char]);
}

function convertPathsToLinks(str) {
  function generateLinks(match, ...args) {
    const parts = match.split("/");

    if (!parts[0]) parts.shift();
    let conc = "";
    let html = "";
    for (let part of parts) {
      conc += "/" + part;
      html += `/<a href="#" class="path-link" onclick="openFileLink('${conc}');">${part}</a>`;
    }
    return html;
  }

  const prefix = `(?:^|[ \`'"\\n]|&#39;|&quot;)`; // Use a non-capturing group for OR logic
  const folder = `[a-zA-Z0-9_\\/.\\-]`; // Characters allowed in folder chain
  const file = `[a-zA-Z0-9_\\-\\/]`; // Characters allowed in file names
  const suffix = `(?<!\\.)`;

  const regex = new RegExp(`(?<=${prefix})\\/${folder}*${file}${suffix}`, "g");

  return str.replace(regex, generateLinks);
}