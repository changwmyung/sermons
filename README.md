# 주일 설교 노트 (Weekly Sermons)

매주일 예배 설교의 자동 전사 + 요약 모음. Hugo 정적 사이트로 GitHub Pages에 배포됩니다.

## Publish

```bash
python3 publish_sermon.py /path/to/sermon.md --verify
```

스크립트가 `content/<slug>.md`로 기록하고 git push → GitHub Actions가 빌드해서
https://changwmyung.github.io/sermons/ 에 배포합니다.

## Local preview

```bash
hugo server -D
```

## Why separate from weekly-blogs?

연구 다이제스트(weekly-blogs)와 개인적 신앙 노트의 청중·맥락이 다르기 때문에 분리.
