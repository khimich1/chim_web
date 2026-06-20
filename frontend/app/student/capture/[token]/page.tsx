import { CapturePage } from "@/components/homework/CapturePage";

interface PageProps {
  params: Promise<{ token: string }>;
}

export default async function StudentCapturePage({ params }: PageProps) {
  const { token } = await params;
  return <CapturePage token={token} />;
}
