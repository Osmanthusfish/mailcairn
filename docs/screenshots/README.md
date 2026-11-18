# Screenshot evidence / 截图说明

`alpha8-reader-retry-zh.png` was captured from the actual Alpha.8 Windows EXE (SHA-256 `9a11ab42700477f9d0f30481988b2802ec40a345fea2865ca3d64ceca7b8efba`) using ego-browser at 1280×800 after importing the public synthetic `tests/fixtures/sample.mbox` (20 messages) and blocking only that test Page's `/api/messages/2` request through CDP. It shows the bilingual in-place retry action (`重试`) inside the reading pane before unblocking and pressing `Enter` to recover the message. Pixels were viewed.

`alpha7-reader-dark-320.png` was captured from the actual Alpha.7 Windows EXE (SHA-256 `7c574d2e0cf16e87880ec90ec4184b49f0fc936c2829da786d55b9e9298c3ac3`) using ego-browser at a 320×568 simulated viewport (document scrollWidth 305px, no horizontal overflow) after setting Lamplight (dark), Large reading type (20px computed `.reader-body`), Compact spacing and Simplified Chinese on the public synthetic 20-message `sample.mbox` archive. Capture waited for `.reader-body`, `.message-flight` removal, all finite Web Animations completion and reader transform `none`; pixels were viewed. This does not establish physical-phone behavior, screen-reader output or owner visual approval.

`alpha6-startup-recovery-en.png` was captured from the actual Alpha.6 Windows EXE (SHA-256 `59ce87b4b7fe458ab14327e52817f23a391f2427b3187aeba745effbe2e3f332`) using ego-browser. Only that synthetic Page's app.js request was temporarily blocked through CDP; the independent panel appeared, the block was removed, and Enter reloaded successfully with two stored synthetic messages. No global network/proxy change was made. Pixels were viewed; this demonstrates error recovery, not the cause of the earlier sporadic startup observation. Alpha.5 reader images below remain explicitly scoped to that build.

The `alpha5-*` images were captured on 2026-11-16 using **ego-browser against the actual Alpha.5 Windows EXE**, SHA-256 `32a5d73df73efd2f9d2361fbb1d325fd7811a32e19d49b30065e28044895bd67`. They contain only the public synthetic `tests/fixtures/sample.mbox` (20 emails, seven attachments), imported through the real UI into an isolated archive. These are application captures, not image-generated mockups.

- `alpha5-home-zh.png`: empty archive, Chinese interface, daylight theme.
- `alpha5-reader-zh.png` / `alpha5-reader-en.png`: same stored mail, Chinese/English interface at 1440×1080; original message text is not translated.
- `alpha5-reader-en-narrow.png`: 390×844 simulated viewport; opening from the list positions the reader at the viewport top. Document width was 375px, with no horizontal overflow. This is not physical-mobile evidence.

Reader captures waited for `.message-flight` to disappear and all finite Web Animations to settle; the reader transform was `none`. The pixels were viewed before inclusion. They do not establish frame rate, low-end hardware performance, full accessibility conformance or owner visual approval. Older files are historical screenshots, not proof of the current build.

中文：alpha5前缀截图来自实际Windows候选和真实界面导入，只含公开合成邮件。截图等候实际入场动画结束后拍摄并人工查看；中英界面使用同一封原邮件，不翻译其内容。窄屏是浏览器模拟，不是手机实测。其他图片保留历史版本范围，不代表用户已认可当前视觉。
