import asyncio
import json
import time
from typing import Optional, List, Dict
from agent import Agent, InterventionException
from pathlib import Path
import os

import models
from python.helpers.tool import Tool, Response
from python.helpers import files, defer, persist_chat, strings
from python.helpers.browser_use import browser_use
from python.helpers.print_style import PrintStyle
from python.helpers.playwright import ensure_playwright_binary
from playwright.async_api import Download as PlaywrightDownload, Page as PlaywrightPage, Response as PlaywrightResponse
from python.extensions.message_loop_start._10_iteration_no import get_iter_no
from pydantic import BaseModel
import uuid
from python.helpers.dirty_json import DirtyJson

MAX_DUPLICATE_PREVENTION_WINDOW_SEC = 5

class State:
    @staticmethod
    async def create(agent: Agent):
        state = State(agent)
        return state

    def __init__(self, agent: Agent):
        self.agent = agent
        self.browser_session: Optional[browser_use.BrowserSession] = None
        self.task: Optional[defer.DeferredTask] = None
        self.use_agent: Optional[browser_use.Agent] = None
        self.iter_no = 0
        self.auto_download_extensions: List[str] = [".pdf"]
        self.downloads_path: Optional[str] = None
        self.recently_handled_urls: Dict[str, float] = {}

    async def _log_to_file(self, message: str):
        try:
            with open('/a0/browser_agent_debug_log.txt', 'a') as f:
                f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [BrowserAgent Internal Debug] {message}\n")
        except Exception as e:
            PrintStyle().error(f"Failed to write to debug log file: {e}") # Fallback if file logging fails

    def __del__(self):
        self.kill_task()

    async def _is_recently_handled(self, url: str) -> bool:
        now = time.time()
        self.recently_handled_urls = {
            u: ts for u, ts in self.recently_handled_urls.items()
            if now - ts < MAX_DUPLICATE_PREVENTION_WINDOW_SEC
        }
        if url in self.recently_handled_urls:
            PrintStyle().info(f"[BrowserAgent Debug] URL {url} was recently handled. Skipping duplicate download attempt.")
            return True
        return False

    async def _mark_as_handled(self, url: str):
        self.recently_handled_urls[url] = time.time()
        PrintStyle().info(f"[BrowserAgent Debug] Marked {url} as recently handled.")

    async def _save_file(self, filename_suggestion: str, content_bytes: Optional[bytes] = None, download_obj: Optional[PlaywrightDownload] = None, source_url: str = "Unknown"):
        await self._log_to_file(f"_save_file: Attempting to save file: {filename_suggestion} from {source_url}")
        await self._log_to_file(f"_save_file: Downloads path configured: {self.downloads_path}")

        if not self.downloads_path:
            await self._log_to_file("WARNING: Downloads path not configured. Cannot save file.")
            return None

        safe_filename = "".join(c if c.isalnum() or c in ['.', '-', '_'] else '_' for c in filename_suggestion)
        if not safe_filename:
            file_extension = Path(filename_suggestion).suffix.lower() or Path(source_url).suffix.lower()
            safe_filename = f"downloaded_file_{uuid.uuid4().hex}{file_extension or '.unknown'}"

        save_path = os.path.join(self.downloads_path, safe_filename)
        await self._log_to_file(f"_save_file: Initial save path: {save_path}")

        counter = 1
        original_save_path_stem, original_save_path_ext = os.path.splitext(save_path)
        while os.path.exists(save_path):
            save_path = f"{original_save_path_stem}_{counter}{original_save_path_ext}"
            counter += 1
        await self._log_to_file(f"_save_file: Final save path after uniqueness check: {save_path}")
        
        try:
            if download_obj:
                await self._log_to_file(f"_save_file: Calling download_obj.save_as({save_path})")
                await download_obj.save_as(save_path)
                await self._log_to_file(f"_save_file: download_obj.save_as completed.")
            elif content_bytes is not None:
                await self._log_to_file(f"_save_file: Opening {save_path} for writing content bytes. Content length: {len(content_bytes)}")
                with open(save_path, "wb") as f:
                    f.write(content_bytes)
                await self._log_to_file(f"_save_file: Content bytes written to {save_path}.")
            else:
                await self._log_to_file("ERROR: No content or download object provided to _save_file.")
                return None

            await self._log_to_file(f"_save_file: Successfully saved: {Path(save_path).name} to {self.downloads_path} (from URL: {source_url})")
            return save_path
        except Exception as e:
            await self._log_to_file(f"_save_file: ERROR: Exception during saving {safe_filename} (from {source_url}): {e}")
            if os.path.exists(save_path) and content_bytes is not None:
                try:
                    os.remove(save_path)
                    await self._log_to_file(f"_save_file: WARNING: Cleaned up partial file: {save_path}")
                except Exception as del_e:
                    await self._log_to_file(f"_save_file: ERROR: Error cleaning up partially saved file {save_path}: {del_e}")
            return None

    async def _handle_automatic_download_event(self, download: PlaywrightDownload, page_url_of_trigger: Optional[str]):
        if not page_url_of_trigger:
            page_url_of_trigger = getattr(download, 'url', None) or download.suggested_filename
            if not page_url_of_trigger.startswith(('http://', 'https://', 'file://')):
                PrintStyle().warning(f"Download event triggered with no clear source URL, using suggested filename: {download.suggested_filename}")

        if page_url_of_trigger and await self._is_recently_handled(page_url_of_trigger):
            try:
                await download.delete()
                PrintStyle().info(f"Download for {download.suggested_filename} (from {page_url_of_trigger}) cancelled as it was recently handled.")
            except Exception as e:
                PrintStyle().warning(f"Could not cancel/delete duplicate download {download.suggested_filename}: {e}")
            return

        suggested_filename = download.suggested_filename
        file_extension = Path(suggested_filename).suffix.lower()

        if file_extension in self.auto_download_extensions:
            PrintStyle().info(f"'download' event: Handling {suggested_filename} from {page_url_of_trigger or 'unknown URL'}")
            saved_path = await self._save_file(
                filename_suggestion=suggested_filename,
                download_obj=download,
                source_url=page_url_of_trigger or suggested_filename
            )
            if saved_path and page_url_of_trigger:
                await self._mark_as_handled(page_url_of_trigger)

    async def _handle_direct_file_response(self, response: PlaywrightResponse):
        url = response.url
        file_extension = Path(url).suffix.lower()

        PrintStyle().info(f"[BrowserAgent Debug] _handle_direct_file_response called for URL: {url}")
        PrintStyle().info(f"[BrowserAgent Debug] File extension: {file_extension}")

        if file_extension not in self.auto_download_extensions:
            PrintStyle().info(f"[BrowserAgent Debug] File extension {file_extension} not in auto_download_extensions. Skipping.")
            return

        if not response.ok:
            PrintStyle().info(f"[BrowserAgent Debug] Response for {url} not OK (status: {response.status}). Skipping direct download.")
            return

        content_type = response.headers.get("content-type", "").lower()
        if file_extension == ".pdf" and "application/pdf" not in content_type:
            PrintStyle().info(f"[BrowserAgent Debug] URL {url} ends with .pdf but Content-Type is '{content_type}'. Skipping.")
            return
        if file_extension in [".jpg", ".jpeg"] and "image/jpeg" not in content_type and "image/jpg" not in content_type :
            PrintStyle().info(f"[BrowserAgent Debug] URL {url} ends with {file_extension} but Content-Type is '{content_type}'. Skipping.")
            return
        if file_extension == ".png" and "image/png" not in content_type:
            PrintStyle().info(f"[BrowserAgent Debug] URL {url} ends with .png but Content-Type is '{content_type}'. Skipping.")
            return
        
        PrintStyle().info(f"[BrowserAgent Debug] Content-Type header: {content_type}")

        is_handled = await self._is_recently_handled(url)
        if is_handled:
            PrintStyle().info(f"[BrowserAgent Debug] URL {url} recently handled. Skipping duplicate saving.")
            return

        PrintStyle().info(f"[BrowserAgent Debug] 'response' event: Handling direct file URL: {url} for saving.")
        try:
            PrintStyle().info(f"[BrowserAgent Debug] Attempting to get response body for {url}.")
            content_bytes = await response.body()
            PrintStyle().info(f"[BrowserAgent Debug] Received {len(content_bytes) if content_bytes else 0} bytes for {url}.")
            if not content_bytes:
                PrintStyle().warning(f"[BrowserAgent Debug] No content bytes received for {url}. Skipping.")
                return

            PrintStyle().info(f"[BrowserAgent Debug] Calling _save_file for {url}.")

            filename = Path(url).name
            saved_path = await self._save_file(
                filename_suggestion=filename,
                content_bytes=content_bytes,
                source_url=url
            )
            if saved_path:
                await self._mark_as_handled(url)
                PrintStyle().info(f"[BrowserAgent Debug] Successfully saved {saved_path} and marked {url} as handled.")

        except Exception as e:
            PrintStyle().error(f"Error processing direct file response for {url}: {e}")

    async def _initialize(self):
        if self.browser_session:
            return

        pw_binary = ensure_playwright_binary()
        self.downloads_path = files.get_abs_path("tmp/downloads")
        files.make_dirs(self.downloads_path)

        self.browser_session = browser_use.BrowserSession(
            browser_profile=browser_use.BrowserProfile(
                headless=True,
                disable_security=True,
                chromium_sandbox=False,
                accept_downloads=True,
                downloads_dir=self.downloads_path, 
                downloads_path=self.downloads_path,
                executable_path=pw_binary,
                keep_alive=True,
                minimum_wait_page_load_time=1.0,
                wait_for_network_idle_page_load_time=2.0,
                maximum_wait_page_load_time=10.0,
                screen={"width": 1024, "height": 2048},
                viewport={"width": 1024, "height": 2048},
                args=["--headless=new"],
            )
        )

        await self.browser_session.start()

        if self.browser_session.browser_context:
            js_override = files.get_abs_path("lib/browser/init_override.js")
            await self.browser_session.browser_context.add_init_script(path=js_override)

            async def page_creation_handler(page: PlaywrightPage):
                page_initial_url = page.url
                PrintStyle().info(f"New page created/navigated: {page_initial_url}. Attaching handlers.")
                
                async def on_download_event_wrapper(download_item: PlaywrightDownload):
                    triggering_page_url = page.url
                    await self._handle_automatic_download_event(download_item, triggering_page_url)

                if not page.is_closed():
                    page.on("download", on_download_event_wrapper)
                    
                    async def on_request_finished_wrapper(request):
                        response = await request.response()
                        if response:
                            await self._handle_direct_file_response(response)
                    
                    page.on("requestfinished", on_request_finished_wrapper)
                else:
                    PrintStyle().warning(f"Page {page_initial_url} was closed before attaching handlers.")

            async def route_force_download(route):
                if route.request.url.lower().endswith(tuple(self.auto_download_extensions)):
                    try:
                        response = await route.fetch()
                        if response:
                            headers = response.headers.copy()
                            headers['content-disposition'] = 'attachment'
                            PrintStyle().info(f"Forcing download for {route.request.url} with Content-Disposition: attachment")
                            await route.fulfill(
                                response=response,
                                headers=headers,
                                body=await response.body()
                            )
                        else:
                            PrintStyle().warning(f"No response received for {route.request.url}. Continuing without modification.")
                            await route.continue_()
                    except Exception as e:
                        PrintStyle().error(f"Error in route_force_download for {route.request.url}: {e}")
                        await route.continue_()
                else:
                    await route.continue_()

            self.browser_session.browser_context.on("page", page_creation_handler)
            
            initial_page = await self.browser_session.get_current_page()
            if initial_page and not initial_page.is_closed():
                 await page_creation_handler(initial_page)
    
    def start_task(self, task: str):
        if self.task and self.task.is_alive():
            self.kill_task()

        self.task = defer.DeferredTask(
            thread_name="BrowserAgent" + self.agent.context.id
        )
        if self.agent.context.task:
            self.agent.context.task.add_child_task(self.task, terminate_thread=True)
        
        async def run_wrapper(task_str):
            await self._initialize()
            PrintStyle().info(f"[BrowserAgent Debug] _run_task: Starting task for message: {task_str[:50]}...")
            return await self._run_task(task_str)

        self.task.start_task(run_wrapper, task) 
        return self.task

    def kill_task(self):
        if self.task:
            self.task.kill(terminate_thread=True)
            self.task = None
        if self.browser_session:
            try:
                async def _close_session():
                    if self.browser_session:
                        if self.browser_session.browser_context and not self.browser_session.browser_context.is_closed():
                             await self.browser_session.close()
                        elif self.browser_session.browser and self.browser_session.browser.is_connected():
                             await self.browser_session.browser.close()
                
                try:
                    current_loop = asyncio.get_running_loop()
                    if current_loop.is_running() and not current_loop.is_closed():
                         asyncio.create_task(_close_session())
                    else:
                         asyncio.run(_close_session())
                except RuntimeError:
                     asyncio.run(_close_session())

            except Exception as e:
                PrintStyle().error(f"Error closing browser session in kill_task: {e}")
            finally:
                self.browser_session = None
        self.use_agent = None
        self.iter_no = 0

    async def _run_task(self, task: str):
        class DoneResult(BaseModel):
            title: str
            response: str
            page_summary: str

        controller = browser_use.Controller(output_model=DoneResult)

        @controller.registry.action("Complete task", param_model=DoneResult)
        async def complete_task(params: DoneResult):
            result = browser_use.ActionResult(
                is_done=True, success=True, extracted_content=params.model_dump_json()
            )
            return result

        class ExtractImageParams(BaseModel):
            selector: str
            filename_suggestion: Optional[str] = None

        @controller.registry.action("Extract image by selector", param_model=ExtractImageParams)
        async def extract_image_by_selector(params: ExtractImageParams):
            await self._log_to_file(f"Action 'Extract image by selector' invoked for selector: {params.selector}")
            page = await self.get_page()
            if not page:
                PrintStyle().error("[BrowserAgent Debug] No active page available to extract image.")
                return browser_use.ActionResult(success=False, error="No active page available to extract image.")

            try:
                image_url = await page.evaluate(f"document.querySelector('{params.selector}').src")
                await self._log_to_file(f"Extracted image URL: {image_url}")
                if not image_url:
                    await self._log_to_file(f"ERROR: Could not find src attribute for selector: {params.selector}")
                    return browser_use.ActionResult(success=False, error=f"Could not find src attribute for selector: {params.selector}")

                response = await page.request.get(image_url)
                await self._log_to_file(f"Image fetch response status: {response.status}")
                if not response.ok:
                    await self._log_to_file(f"ERROR: Failed to fetch image from {image_url} (status: {response.status})")
                    return browser_use.ActionResult(success=False, error=f"Failed to fetch image from {image_url} (status: {response.status})")

                content_bytes = await response.body()
                await self._log_to_file(f"Received content bytes length: {len(content_bytes) if content_bytes else 0}")
                if not content_bytes:
                    await self._log_to_file(f"ERROR: No content received for image from {image_url}")
                    return browser_use.ActionResult(success=False, error=f"No content received for image from {image_url}")

                suggested_filename = params.filename_suggestion or Path(image_url).name
                if not suggested_filename:
                    suggested_filename = f"extracted_image_{uuid.uuid4().hex}{Path(image_url).suffix or '.bin'}"

                await self._log_to_file(f"Calling _save_file for {suggested_filename}, content_bytes length: {len(content_bytes) if content_bytes else 0}, source_url: {image_url}")
                saved_path = await self._save_file(
                    filename_suggestion=suggested_filename,
                    content_bytes=content_bytes,
                    source_url=image_url
                )

                if saved_path:
                    await self._log_to_file(f"Image saved successfully to: {saved_path}")
                    return browser_use.ActionResult(success=True, extracted_content=f"Successfully extracted image to: {saved_path}")
                else:
                    await self._log_to_file(f"ERROR: Failed to save image from {image_url}. _save_file returned None.")
                    return browser_use.ActionResult(success=False, error=f"Failed to save image from {image_url}")

            except Exception as e:
                await self._log_to_file(f"ERROR: Error extracting image: {e}")
                return browser_use.ActionResult(success=False, error=f"Error extracting image: {e}")

        model = models.get_model(
            type=models.ModelType.CHAT,
            provider=self.agent.config.browser_model.provider,
            name=self.agent.config.browser_model.name,
            **self.agent.config.browser_model.kwargs,
        )

        if not self.browser_session or not self.browser_session.browser_context:
            PrintStyle().error("Browser session not properly initialized for _run_task.")
            raise InterventionException("Browser session initialization failed.")

        self.use_agent = browser_use.Agent(
            task=task,
            browser_session=self.browser_session,
            llm=model,
            use_vision=self.agent.config.browser_model.vision,
            extend_system_message=self.agent.read_prompt(
                "prompts/browser_agent.system.md"
            ),
            controller=controller,
            enable_memory=False,
        )

        self.iter_no = get_iter_no(self.agent)

        async def hook(agent: browser_use.Agent):
            await self.agent.wait_if_paused()
            if self.iter_no != get_iter_no(self.agent):
                raise InterventionException("Task cancelled")

        result = await self.use_agent.run(
            max_steps=50, on_step_start=hook, on_step_end=hook
        )
        return result
    
    async def get_page(self):
        if self.use_agent and self.browser_session:
            try:
                current_page = await self.use_agent.browser_session.get_current_page()
                if current_page and not current_page.is_closed():
                    return current_page
                else:
                    if self.browser_session.browser_context and self.browser_session.browser_context.pages:
                        for p in reversed(self.browser_session.browser_context.pages):
                            if not p.is_closed():
                                return p
                    PrintStyle().warning("Attempted to get page, but no valid page found or current page is closed.")
                    return None
            except Exception as e:
                PrintStyle().error(f"Error getting current page: {e}")
                return None
        return None

    async def get_selector_map(self):
        page = await self.get_page()
        if self.use_agent and page:
            try:
                await self.use_agent.browser_session.get_state_summary(
                    cache_clickable_elements_hashes=True
                )
                return await self.use_agent.browser_session.get_selector_map()
            except Exception as e:
                PrintStyle().error(f"Error getting selector map: {e}")
                return {}
        return {}


class BrowserAgent(Tool):

    async def execute(self, message="", reset="", **kwargs):
        with open('/a0/test_browser_agent_activation.txt', 'w') as f: f.write('Browser agent activated from modified script.\n')
        PrintStyle().info("[BrowserAgent Debug] Starting BrowserAgent.execute method - File creation attempted.")
        self.guid = str(uuid.uuid4())
        reset = str(reset).lower().strip() == "true"
        await self.prepare_state(reset=reset)
        task = self.state.start_task(message)

        timeout_seconds = 300
        start_time = time.time()

        fail_counter = 0
        while not task.is_ready():
            if time.time() - start_time > timeout_seconds:
                PrintStyle().warning(
                    f"Browser agent task timeout after {timeout_seconds} seconds, forcing completion"
                )
                break

            await self.agent.handle_intervention()
            await asyncio.sleep(1)
            try:
                if task.is_ready():
                    break
                try:
                    update = await asyncio.wait_for(self.get_update(), timeout=10)
                    fail_counter = 0
                except asyncio.TimeoutError:
                    fail_counter += 1
                    PrintStyle().warning(
                        f"browser_agent.get_update timed out ({fail_counter}/3)"
                    )
                    if fail_counter >= 3:
                        PrintStyle().warning(
                            "3 consecutive browser_agent.get_update timeouts, breaking loop"
                        )
                        break
                    continue
                log = update.get("log", get_use_agent_log(None))
                self.update_progress("\n".join(log))
                screenshot = update.get("screenshot", None)
                if screenshot:
                    self.log.update(screenshot=screenshot)
            except Exception as e:
                PrintStyle().error(f"Error getting update: {str(e)}")

        if not task.is_ready():
            PrintStyle().warning("browser_agent.get_update timed out, killing the task")
            self.state.kill_task()
            return Response(
                message="Browser agent task timed out, not output provided.",
                break_loop=False,
            )

        if self.state.use_agent:
            log = get_use_agent_log(self.state.use_agent)
            self.update_progress("\n".join(log))

        try:
            result = await task.result()
        except Exception as e:
            PrintStyle().error(f"Error getting browser agent task result: {str(e)}")
            answer_text = f"Browser agent task failed to return result: {str(e)}"
            self.log.update(answer=answer_text)
            return Response(message=answer_text, break_loop=False)

        if result.is_done():
            answer = result.final_result()
            try:
                if answer and isinstance(answer, str) and answer.strip():
                    answer_data = DirtyJson.parse_string(answer)
                    answer_text = strings.dict_to_text(answer_data)
                else:
                    answer_text = (
                        str(answer) if answer else "Task completed successfully"
                    )
            except Exception as e:
                answer_text = (
                    str(answer)
                    if answer
                    else f"Task completed with parse error: {str(e)}"
                )
        else:
            urls = result.urls()
            current_url = urls[-1] if urls else "unknown"
            answer_text = (
                f"Task reached step limit without completion. Last page: {current_url}. "
                f"The browser agent may need clearer instructions on when to finish."
            )
        
        self.log.update(answer=answer_text)

        if self.log.kvps and "screenshot" in self.log.kvps and self.log.kvps['screenshot']:
            path = self.log.kvps['screenshot'].split('//', 1)[-1].split('&', 1)[0]
            answer_text += f"\n\nScreenshot: {path}"

        return Response(message=answer_text, break_loop=False)

    def get_log_object(self):
        return self.agent.context.log.log(
            type="browser",
            heading=f"{self.agent.agent_name}: Using tool '{self.name}'",
            content="",
            kvps=self.args,
        )

    async def get_update(self):
        await self.prepare_state()

        result = {}
        agent = self.agent
        ua = self.state.use_agent
        page = await self.state.get_page()

        if ua and page:
            try:
                async def _get_update():
                    log = []
                    result["log"] = get_use_agent_log(ua)

                    path = files.get_abs_path(
                        persist_chat.get_chat_folder_path(agent.context.id),
                        "browser",
                        "screenshots",
                        f"{self.guid}.png",
                    )
                    files.make_dirs(path)
                    await page.screenshot(path=path, full_page=False, timeout=3000)
                    result["screenshot"] = f"img://{path}&t={str(time.time())}"

                if self.state.task and not self.state.task.is_ready():
                    await self.state.task.execute_inside(_get_update)

            except Exception:
                pass

        return result

    async def prepare_state(self, reset=False):
        self.state = self.agent.get_data("_browser_agent_state")
        if reset and self.state:
            self.state.kill_task()
        if not self.state or reset:
            self.state = await State.create(self.agent)
        self.agent.set_data("_browser_agent_state", self.state)

    def update_progress(self, text):
        short = text.split("\n")[-1]
        if len(short) > 50:
            short = short[:50] + "..."
        progress = f"Browser: {short}"

        self.log.update(progress=text)
        self.agent.context.log.set_progress(progress)

def get_use_agent_log(use_agent: browser_use.Agent | None):
    result = ["🚦 Starting task"]
    if use_agent:
        action_results = use_agent.state.history.action_results()
        short_log = []
        for item in action_results:
            if item.is_done:
                if item.success:
                    short_log.append(f"✅ Done")
                else:
                    short_log.append(f"❌ Error: {item.error or item.extracted_content or 'Unknown error'}")
            else:
                text = item.extracted_content
                if text:
                    first_line = text.split("\n", 1)[0][:200]
                    short_log.append(first_line)
        result.extend(short_log)
    return result
