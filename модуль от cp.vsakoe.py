# ---------------------------------------------------------------------------------
#  /\_/\  🌐 Этот модуль переведен каналом @hikktutor
# ---------------------------------------------------------------------------------
# Name: autoprofile
# Description: Автоматическое изменение вашего профиля
# Автор: GeekTG
# Перевод:@hikktutor
# .autopfp      | .stopautopfp | .autobio | .stopautobio | .autoname
# .stopautoname | .delpfp
# ---------------------------------------------------------------------------------


# -*- coding: utf-8 -*-

import ast
import asyncio
import time
from io import BytesIO

from telethon.tl import functions

from .. import loader, utils

try:
    from PIL import Image
except ImportError:
    pil_installed = False
else:
    pil_installed = True


@loader.tds
class AutoProfileMod(loader.Module):
    """Автоматическое изменение вашего профиля
    перевод @hikktutor"""

    strings = {
        "name": "Automatic Profile",
        "missing_pil": "<b>У вас не установлен Pillow </b>",
        "missing_pfp": "<b>Отсутствует фото профиля для вращения </b>",
        "invalid_args": "<b>Отсутствую параметры, прочитайте инструкцию</b>",
        "invalid_degrees": (
            "<b>Не допустимое количество градусов для поворота</b>"
        ),
        "invalid_delete": (
            "<b>Пожалуйста, укажите, удалять старые фотографии или нет</b>"
        ),
        "enabled_pfp": "<b>Включен поворот изображения профиля</b>",
        "pfp_not_enabled": "<b> Поворот изображения профиля не включен</b>",
        "pfp_disabled": "<b>Поворот изображения профиля отключен</b>",
        "missing_time": "<b>Время не было указано в био</b>",
        "enabled_bio": "<b>Био часы включены</b>",
        "bio_not_enabled": "<b>Био часы не включены</b>",
        "disabled_bio": "<b>Био часы выключены</b>",
        "enabled_name": "<b>Часы в нике включены</b>",
        "name_not_enabled": "<b>Часы в нике не включены</b>",
        "disabled_name": "<b>Часы в нике выключены</b>",
        "how_many_pfps": (
            "<b>Укажите сколько аватарок нужно удалить</b>"
        ),
        "invalid_pfp_count": "<b>Недопустимое количество аватарок для удаления</b>",
        "removed_pfps": "<b>Удалено {} аватарок</b>",
    }

    def __init__(self):
        self.client = None
        self.bio_enabled = False
        self.name_enabled = False
        self.pfp_enabled = False
        self.raw_bio = None
        self.raw_name = None

    async def client_ready(self, client, db):
        self.client = client

    async def autopfpcmd(self, message):
        """Поворачивает аватар каждые 60 секунд на x градусов, использование:
        .autopfp <градусы> <remove previous (last pfp)>

        градусы - 60, -10, etc
        Убрать последний pfp - да/1/нет/0, с учетом регистра"""

        if not pil_installed:
            return await utils.answer(message, self.strings("missing_pil", message))

        if not await self.client.get_profile_photos("me", limit=1):
            return await utils.answer(message, self.strings("missing_pfp", message))

        msg = utils.get_args(message)
        if len(msg) != 2:
            return await utils.answer(message, self.strings("invalid_args", message))

        try:
            degrees = int(msg[0])
        except ValueError:
            return await utils.answer(message, self.strings("invalid_degrees", message))

        try:
            delete_previous = ast.literal_eval(msg[1])
        except (ValueError, SyntaxError):
            return await utils.answer(message, self.strings("invalid_delete", message))

        with BytesIO() as pfp:
            await self.client.download_profile_photo("me", file=pfp)
            raw_pfp = Image.open(pfp)

            self.pfp_enabled = True
            pfp_degree = 0
            await self.allmodules.log("start_autopfp")
            await utils.answer(message, self.strings("enabled_pfp", message))

            while self.pfp_enabled:
                pfp_degree = (pfp_degree + degrees) % 360
                rotated = raw_pfp.rotate(pfp_degree)
                with BytesIO() as buf:
                    rotated.save(buf, format="JPEG")
                    buf.seek(0)

                    if delete_previous:
                        await self.client(
                            functions.photos.DeletePhotosRequest(
                                await self.client.get_profile_photos("me", limit=1)
                            )
                        )

                    await self.client(
                        functions.photos.UploadProfilePhotoRequest(
                            await self.client.upload_file(buf)
                        )
                    )
                    buf.close()
                await asyncio.sleep(60)

    async def stopautopfpcmd(self, message):
        """Остановить часы био."""

        if self.pfp_enabled is False:
            return await utils.answer(message, self.strings("pfp_not_enabled", message))
        self.pfp_enabled = False

        await self.client(
            functions.photos.DeletePhotosRequest(
                await self.client.get_profile_photos("me", limit=1)
            )
        )
        await self.allmodules.log("stop_autopfp")
        await utils.answer(message, self.strings("pfp_disabled", message))

    async def autobiocmd(self, message):
        """Автоматически изменяет биографию вашего аккаунта с указанием текущего времени, использования:
        .autobio '<message, time as {time}>'"""

        msg = utils.get_args(message)
        if len(msg) != 1:
            return await utils.answer(message, self.strings("invalid_args", message))
        raw_bio = msg[0]
        if "{time}" not in raw_bio:
            return await utils.answer(message, self.strings("missing_time", message))

        self.bio_enabled = True
        self.raw_bio = raw_bio
        await self.allmodules.log("start_autobio")
        await utils.answer(message, self.strings("enabled_bio", message))

        while self.bio_enabled:
            current_time = time.strftime("%H:%M")
            bio = raw_bio.format(time=current_time)
            await self.client(functions.account.UpdateProfileRequest(about=bio))
            await asyncio.sleep(60)

    async def stopautobiocmd(self, message):
        """Остановить автобиографию cmd."""

        if self.bio_enabled is False:
            return await utils.answer(message, self.strings("bio_not_enabled", message))
        self.bio_enabled = False
        await self.allmodules.log("stop_autobio")
        await utils.answer(message, self.strings("disabled_bio", message))
        await self.client(
            functions.account.UpdateProfileRequest(about=self.raw_bio.format(time=""))
        )

    async def autonamecmd(self, message):
        """Автоматически изменяет ваше имя Telegram с учетом текущего времени, использования:
        .autoname '<сообщение, время как {time}>'"""

        msg = utils.get_args(message)
        if len(msg) != 1:
            return await utils.answer(message, self.strings("invalid_args", message))
        raw_name = msg[0]
        if "{time}" not in raw_name:
            return await utils.answer(message, self.strings("missing_time", message))

        self.name_enabled = True
        self.raw_name = raw_name
        await self.allmodules.log("start_autoname")
        await utils.answer(message, self.strings("enabled_name", message))

        while self.name_enabled:
            current_time = time.strftime("%H:%M")
            name = raw_name.format(time=current_time)
            await self.client(functions.account.UpdateProfileRequest(first_name=name))
            await asyncio.sleep(60)

    async def stopautonamecmd(self, message):
        """Остановить команду autoname."""

        if self.name_enabled is False:
            return await utils.answer(
                message, self.strings("name_not_enabled", message)
            )
        self.name_enabled = False
        await self.allmodules.log("stop_autoname")
        await utils.answer(message, self.strings("disabled_name", message))
        await self.client(
            functions.account.UpdateProfileRequest(
                first_name=self.raw_name.format(time="")
            )
        )

    async def delpfpcmd(self, message):
        """Удалить x-изображение(я) из вашего профиля.
        .delpfp <количество кадров/неограниченно - удалить все>"""

        args = utils.get_args(message)
        if not args:
            return await utils.answer(message, self.strings("how_many_pfps", message))
        try:
            pfps_count = int(args[0])
        except ValueError:
            return await utils.answer(
                message, self.strings("invalid_pfp_count", message)
            )
        if pfps_count < 0:
            return await utils.answer(
                message, self.strings("invalid_pfp_count", message)
            )
        if pfps_count == 0:
            pfps_count = None

        to_delete = await self.client.get_profile_photos("me", limit=pfps_count)
        await self.client(functions.photos.DeletePhotosRequest(to_delete))

        await self.allmodules.log("delpfp")
        await utils.answer(
            message, self.strings("removed_pfps", message).format(len(to_delete))
        )
        return await utils.answer(message, self.strings("how_many_pfps", message))