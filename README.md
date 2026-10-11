# Dashboard tiếp nhận AI coding agent

Dashboard FastAPI + Next.js bằng tiếng Việt để tái lập và theo dõi việc tiếp nhận AI coding agent theo Robbes et al. [2] và Njoku, Sharafi, Khomh [3]. Giao diện so sánh số liệu bài báo, kết quả tái lập từ dữ liệu gốc và số liệu mới nhất.

## Yêu cầu

- Python 3.12 và [uv](https://docs.astral.sh/uv/)
- Node.js 22 và npm
- Git có thể khởi tạo submodule `vendor/agent-impact`
- `gh` đã đăng nhập khi đồng bộ GitHub hoặc trao đổi state release

Khởi tạo submodule sau khi clone:

```bash
git submodule update --init --recursive
```

## Biến môi trường

Tạo `backend/.env` hoặc xuất các biến trước khi chạy lệnh backend. Các tệp `.env*` không được commit.

| Biến | Mặc định | Mục đích |
| --- | --- | --- |
| `GITHUB_TOKENS` | token từ `gh auth token` | Một hay nhiều GitHub token, phân tách bằng dấu phẩy. Bắt buộc nếu `gh` chưa đăng nhập. |
| `DATA_DIR` | `../data` | Thư mục lưu state, cache, snapshots và work files. |
| `OPENAI_API_KEY` | — | Tùy chọn; dùng để phân loại task PR không khớp regex. |
| `AGENTDASH_ROLE` | `local-all` | Vai trò thực thi: `local-all`, `local-p2`, hoặc `ci`. |
| `STATE_RELEASE_REPO` | `<owner>/agent-adoption-dashboard` | Repository giữ GitHub Release `state` chứa các SQLite database nén. |
| `P2_CHUNK_SIZE` | `200` | Số repository trong một chunk của pipeline bài [2]. |
| `P2_WORKERS` | `8` | Số worker của pipeline bài [2]. |
| `P3_HUMAN_ENRICH_PCT` | `10` | Phần trăm PR người được enrichment ở panel bài [3]. |
| `START_MONTH` | `2024-01` | Tháng bắt đầu backfill Search API toàn GitHub. |

Frontend dùng `NEXT_PUBLIC_DATA_BASE` để trỏ tới snapshots. Khi phát triển cục bộ, tạo `frontend/.env.local`:

```dotenv
NEXT_PUBLIC_DATA_BASE=http://localhost:8000/api/snapshots
```

## Vai trò chạy

- **`local-all`** (mặc định): máy local có thể chạy toàn bộ nguồn, bao gồm tái lập và live sync bài [2].
- **`local-p2`**: máy local chuyên chạy pipeline bài [2], vốn clone repository và cần nhiều dung lượng đĩa.
- **`ci`**: GitHub Actions chỉ đồng bộ Search API toàn GitHub và panel bài [3]; không chạy bài [2], mà đọc `p2.db` do máy local công bố.

## Chạy cục bộ

Cài phụ thuộc backend:

```bash
cd backend
uv sync
```

Các lệnh dưới đây chạy từ `backend/`:

```bash
# Tái lập baseline của bài [3] từ AIDev v3
uv run agentdash baseline p3

# Nạp snapshot Zenodo của bài [2]
uv run agentdash ingest zenodo

# Phục vụ API và scheduler local
uv run agentdash serve
```

Trong một terminal khác, chạy frontend:

```bash
cd frontend
npm ci
npm run dev
```

Mở ứng dụng tại địa chỉ do Next.js in ra. API local mặc định phục vụ snapshots tại `http://localhost:8000/api/snapshots`.

## Đồng bộ và triển khai

Workflow `.github/workflows/sync.yml` chạy mỗi 6 giờ hoặc từ **workflow_dispatch**. Nó tải state release, đồng bộ nguồn `global` và `p3`, công bố `p3.db.gz` cùng `global.db.gz`, xuất dữ liệu tĩnh và triển khai GitHub Pages.

Thiết lập repository Pages công khai với source **GitHub Actions**, rồi thêm secret `GH_TOKENS` (classic PAT có scope `public_repo`). Workflow dùng `GH_TOKEN` mặc định của GitHub Actions để quản lý release state.

Máy local chạy bài [2] cần công bố `p2.db` lên release state; CI không chạy pipeline này vì yêu cầu clone và hàng chục GiB dung lượng.
