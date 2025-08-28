# 本项目的开发规范

由于普遍AI工具只支持一个文件，暂时只有 [whole.md](whole.md)

你可以通过建立硬链接的方式放置到你的AI助手读取位置

- Gemini - `New-Item -ItemType HardLink -Path "GEMINI.md" -Target "docs/develop/spec/agent_guidelines.md"`
- Qwen - `New-Item -ItemType HardLink -Path "QWEN.md" -Target "docs/develop/spec/agent_guidelines.md"`
- Claude Code - `New-Item -ItemType HardLink -Path "CLAUDE.md" -Target "docs/develop/spec/agent_guidelines.md"`
- Roo Code - `New-Item -ItemType HardLink -Path " .roo/rules-code/project.md" -Target "docs/develop/spec/agent_guidelines.md"`