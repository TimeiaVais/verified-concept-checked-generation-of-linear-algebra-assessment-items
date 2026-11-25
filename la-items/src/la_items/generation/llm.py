"""LLM clients that do not depend on one provider, and the call log every call goes through.

A provider joins later as one small class with `complete(prompt, parameters)`. Until then
`FileReplayClient` returns replies saved in files, for example pasted from any chat.
"""

import collections.abc
import dataclasses
import datetime
import json
import pathlib

from la_items import contracts
from la_items.generation import prompts

__all__ = ["FileReplayClient", "LoggedLlmClient"]


class FileReplayClient:
    """Return the text of the given files as replies, one file per call, in order.

    Parameters
    ----------
    response_files : Sequence[pathlib.Path]
        The replies.
    model, model_version : str
        What to record as the model, for example the chat model the replies came from.
    """

    def __init__(
        self,
        response_files: collections.abc.Sequence[pathlib.Path],
        model: str = "replay",
        model_version: str = "files",
    ) -> None:
        self._remaining = list(response_files)
        self._model = model
        self._model_version = model_version

    def complete(
        self, prompt: str, parameters: collections.abc.Mapping[str, object]
    ) -> contracts.LlmResponse:
        """Return the next saved reply; the prompt is ignored.

        Raises
        ------
        RuntimeError
            It raises when no saved reply is left.
        """
        if not self._remaining:
            raise RuntimeError("no saved reply left")
        text = self._remaining.pop(0).read_text(encoding="utf-8")
        response = contracts.LlmResponse(text, self._model, self._model_version)

        return response


class LoggedLlmClient:
    """Send prompts through a client and append every call to a JSON Lines log.

    Parameters
    ----------
    client : contracts.LlmClient
        The client that talks to the model.
    log_path : pathlib.Path
        The log file. Each line is one `contracts.LlmCall`.
    """

    def __init__(self, client: contracts.LlmClient, log_path: pathlib.Path) -> None:
        self._client = client
        self.log_path = log_path

    def complete(
        self, prompt: prompts.RenderedPrompt, parameters: collections.abc.Mapping[str, object]
    ) -> contracts.LlmResponse:
        """Call the model and log the model, version, parameters, full prompt and full reply.

        Parameters
        ----------
        prompt : prompts.RenderedPrompt
            The prompt and the template it came from.
        parameters : Mapping[str, object]
            The call parameters, for example temperature.

        Returns
        -------
        contracts.LlmResponse
            The reply.
        """
        response = self._client.complete(prompt.text, parameters)
        call = contracts.LlmCall(
            timestamp=datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds"),
            model=response.model,
            model_version=response.model_version,
            parameters=dict(parameters),
            prompt_name=prompt.name,
            prompt_sha256=prompt.template_sha256,
            prompt=prompt.text,
            response=response.text,
        )
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        with self.log_path.open("a", encoding="utf-8") as log:
            log.write(json.dumps(dataclasses.asdict(call), ensure_ascii=False) + "\n")

        return response
