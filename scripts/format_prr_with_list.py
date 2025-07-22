import pandas as pd

def build_grid_with_yaxis(df):
    # 連續的座標範圍
    min_x, max_x = int(df.X_COORD.min()), int(df.X_COORD.max())
    min_y, max_y = int(df.Y_COORD.min()), int(df.Y_COORD.max())
    xs = list(range(min_x, max_x+1))
    ys = list(range(min_y, max_y+1))[::-1]  # y 從大到小

    # 格子寬度 & Y 標籤寬度
    w_x = max(max(len(str(x)) for x in xs),
              max(df.PART_ID.astype(str).map(len)))
    w_y = max(len(str(min_y)), len(str(max_y)))

    # 產生邊框
    def sep(left, mid, right):
        # 第一格是 Y 標籤區 (w_y+2)，其餘是 X 欄位 (w_x+2)
        parts = ['─'*(w_y+2)] + ['─'*(w_x+2) for _ in xs]
        return left + mid.join(parts) + right

    top    = sep('┌','┬','┐')
    midsep = sep('├','┼','┤')
    bot    = sep('└','┴','┘')

    # Header: 空掉 Y 標籤，再列出 X 標頭
    header_cells = [' '*(w_y+2)] + [f' {x:^{w_x}} ' for x in xs]
    header = '│' + '│'.join(header_cells) + '│'

    lines = [top, header, midsep]

    # 每一列：Y 標籤 + 各格內容
    for y in ys:
        row_cells = [f' {y:>{w_y}} ']  # 右對齊 Y
        for x in xs:
            match = df[(df.X_COORD==x)&(df.Y_COORD==y)]
            cell = str(int(match.PART_ID.iloc[0])) if not match.empty else ''
            row_cells.append(f' {cell:^{w_x}} ')
        lines.append('│' + '│'.join(row_cells) + '│')

    lines.append(bot)
    return lines

def build_list_lines(df):
    return [f"x={int(r.X_COORD)} y={int(r.Y_COORD)} and part ID={int(r.PART_ID)}"
            for _, r in df.iterrows()]

if __name__ == "__main__":
    # 讀 CSV
    df = pd.read_csv('output/prr.csv')

    grid = build_grid_with_yaxis(df)
    lst  = build_list_lines(df)

    # 將左側格子和右側列表併列印出
    width = max(len(line) for line in grid)
    for i in range(max(len(grid), len(lst))):
        left  = grid[i] if i < len(grid) else ' '*width
        right = lst[i]  if i < len(lst)  else ''
        print(left.ljust(width) + '   ' + right)
