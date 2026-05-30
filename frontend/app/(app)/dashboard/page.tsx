import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

/**
 * Dashboard route placeholder inside the authenticated `(app)` group
 * (architecture.md §3). Feature content (student ECG dashboard) is a later
 * slice; F1 ships the route so the client-rendered `(app)` shell renders.
 */
export default function DashboardPage() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Bảng điều khiển</CardTitle>
        <CardDescription>
          Nội dung dành cho người dùng đã đăng nhập sẽ được bổ sung ở các slice
          sau (F3–F9).
        </CardDescription>
      </CardHeader>
      <CardContent />
    </Card>
  );
}
